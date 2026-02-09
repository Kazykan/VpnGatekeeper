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
    """
    Первичное создание конфига для нового пользователя и синхронизация его на все Amnezia-серверы.
    Если конфиг уже есть — выполняется логика разблокировки (на случай, если пользователь был заблокирован из-за неуплаты).
    """
    try:
        user = TelegramUser.objects.get(telegram_id=telegram_id)

        # 1. Находим все серверы типа Amnezia, исключая старый сервер
        all_amnezia_servers = Server.objects.filter(type="amnezia").exclude(name__icontains="Old_server")
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

        # Получаем старый сервер для блокировки/разблокировки IP
        old_server = Server.objects.filter(type="amnezia", name__icontains="Old_server").first()

        if credential and credential.wg_conf:
            # СЛУЧАЙ А: Конфиг уже есть — РАЗБЛОКИРОВКА
            ip_match = re.search(r"Address\s*=\s*([\d\.]+)", credential.wg_conf)

            if ip_match:
                client_ip = ip_match.group(1)
                logger.info(
                    f"User {telegram_id} exists. Unblocking IP {client_ip} on OLD server..."
                )

                # Разблокировка только на старом сервере
                if old_server:
                    try:
                        old_gateway = AmneziaGateway(
                            api_url=old_server.api_url,
                            username=old_server.api_username,
                            password=old_server.api_password,
                        )
                        old_gateway.unblock_ip(client_ip)
                        logger.info(f"Successfully unblocked {client_ip} on OLD server")
                    except Exception as e:
                        logger.error(f"Failed to unblock {client_ip} on OLD server: {e}")  # <<< CHANGED

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

            # Рассылаем файлы на Slave-серверы (без старого сервера)
            slave_servers = all_amnezia_servers.exclude(id=master_server.id)  # <<< CHANGED
            for slave in slave_servers:
                try:
                    slave_gateway = AmneziaGateway(
                        api_url=slave.api_url,
                        username=slave.api_username,
                        password=slave.api_password,
                    )

                    if not isinstance(wg_conf_data, str) or not isinstance(clients_table_data, str):
                        logger.error("Master server returned invalid or empty config data")
                        return

                    sync_res = slave_gateway.replace_configs(
                        wg_conf=wg_conf_data, clients_table=clients_table_data
                    )

                    if "error" in sync_res:
                        logger.error(f"Failed to sync slave {slave.name}: {sync_res['error']}")
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
