# myapp/tasks/provisioning.py
import logging
import re
from celery import shared_task
from django.conf import settings
from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
from myapp.models import Credential, Server, TelegramUser

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_vpn_cluster(self, telegram_id):
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)

        # 1. Находим все серверы типа Amnezia
        all_amnezia_servers = Server.objects.filter(type="amnezia")
        master_server = all_amnezia_servers.first()

        if not master_server:
            logger.error("No master server found for synchronization")
            return

        # Инициализируем шлюз для Мастера
        master_gateway = AmneziaGateway(
            api_url=master_server.api_url,
            username=master_server.api_username,
            password=master_server.api_password,
        )

        # 2. Проверяем наличие существующего конфига
        credential = Credential.objects.filter(user=user, server=master_server).first()

        if credential and credential.wg_conf:
            # СЛУЧАЙ А: Конфиг уже есть — РАЗБЛОКИРОВКА
            ip_match = re.search(r"Address\s*=\s*([\d\.]+)", credential.wg_conf)

            if ip_match:
                client_ip = ip_match.group(1)
                logger.info(
                    f"User {telegram_id} exists. Unblocking IP {client_ip} on all servers..."
                )

                # Рассылаем разблокировку на ВСЕ серверы (включая мастер)
                for server in all_amnezia_servers:
                    try:
                        gw = AmneziaGateway(
                            api_url=server.api_url,
                            username=server.api_username,
                            password=server.api_password,
                        )
                        gw.unblock_ip(client_ip)
                        logger.info(
                            f"Successfully unblocked {client_ip} on {server.name}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to unblock {client_ip} on {server.name}: {e}"
                        )

            credential.active = True
            credential.save()

        else:
            # СЛУЧАЙ Б: Конфига нет — СОЗДАНИЕ И СИНХРОНИЗАЦИЯ
            logger.info(f"Creating new config for user {telegram_id} on master...")
            client_name = f"tg_{user.telegram_id}"
            result = master_gateway.create_user(client_name=client_name)

            if isinstance(result, dict) and "error" in result:
                raise Exception(f"Master API Error: {result['error']}")

            # Сохраняем новый конфиг в базу
            credential, created = Credential.objects.update_or_create(
                user=user,
                server=master_server,
                defaults={"wg_conf": result.get("client_conf"), "active": True},
            )

            # Получаем полные данные для синхронизации кластера
            master_configs = master_gateway.get_configs()
            if "error" in master_configs:
                raise Exception(
                    f"Failed to get configs from master: {master_configs['error']}"
                )

            wg_conf_data = master_configs.get("wg_conf")
            clients_table_data = master_configs.get("clients_table")

            # Рассылаем файлы на Slave-серверы
            slave_servers = all_amnezia_servers.exclude(id=master_server.id)
            for slave in slave_servers:
                try:
                    slave_gateway = AmneziaGateway(
                        api_url=slave.api_url,
                        username=slave.api_username,
                        password=slave.api_password,
                    )

                    if not isinstance(wg_conf_data, str) or not isinstance(
                        clients_table_data, str
                    ):
                        logger.error(
                            "Master server returned invalid or empty config data"
                        )
                        return

                    sync_res = slave_gateway.replace_configs(
                        wg_conf=wg_conf_data, clients_table=clients_table_data
                    )

                    if "error" in sync_res:
                        logger.error(
                            f"Failed to sync slave {slave.name}: {sync_res['error']}"
                        )
                    else:
                        logger.info(f"Successfully synced {slave.name}")

                except Exception as e:
                    logger.error(f"Error communicating with slave {slave.name}: {e}")

        # 3. Обработка Xray (без изменений)
        xray_servers = Server.objects.filter(type="xray")
        for xray_srv in xray_servers:
            logger.info(f"Xray config sync logic for {xray_srv.name} (stub)")

    except TelegramUser.DoesNotExist:
        logger.error(f"User with id {telegram_id} not found")
    except Exception as exc:
        logger.error(f"Cluster sync failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
