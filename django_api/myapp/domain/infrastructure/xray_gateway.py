# myapp/domain/infrastructure/xray_gateway.py
import logging
from py3xui import Api, Client
from myapp.domain.infrastructure.telegram_gateway import send_message_to_admin_chanel

logger = logging.getLogger(__name__)


class XrayGateway:
    def __init__(self, api_url, username, password, server_name="Unknown"):
        self.server_name = server_name
        self.api = Api(api_url, username=username, password=password)

        # УДАЛЕН лишний self.api.login(), который стоял здесь раньше.
        # Теперь ошибка логина сразу попадет в блок except и отправится в Telegram.
        try:
            logger.info(f"🔑 Попытка входа на сервер {self.server_name}...")
            self.api.login()
        except Exception as e:
            error_msg = (
                f"❌ <b>Ошибка входа на сервер:</b> {self.server_name}\n"
                f"🌐 URL: {api_url}\n"
                f"⚠️ Error: {str(e)}"
            )
            logger.error(f"Login failed: {error_msg}")
            send_message_to_admin_chanel(error_msg, is_error=True)
            raise

    def upsert_client(
        self, inbound_id: int, client_id: str, email: str, expiry_time: int
    ):
        try:
            # 1. Сначала ПРИНУДИТЕЛЬНО ищем клиента по всему серверу
            existing = None
            try:
                existing = self.api.client.get_by_email(email)
            except Exception:
                pass

            if existing:
                # Если нашли - просто обновляем данные, чтобы они совпадали с нашей БД
                logger.info(f"👤 Клиент {email} найден, синхронизируем данные...")
                existing.id = client_id  # Убеждаемся, что UUID совпадает с нашей БД
                existing.expiry_time = expiry_time
                existing.enable = True
                self.api.client.update(str(existing.id), existing)
                return existing

            # 2. Если get_by_email не нашел, но ошибка Duplicate все равно лезет (защита от глюков панели)
            try:
                new_client = Client(
                    id=client_id,
                    email=email,
                    expiryTime=expiry_time,
                    enable=True,
                    limitIp=0,
                    totalGB=0,
                )
                return self.api.client.add(inbound_id=inbound_id, clients=[new_client])
            except Exception as e:
                if "Duplicate email" in str(e):
                    # Если мы здесь, значит клиент ЕСТЬ, но API его не видит через get_by_email
                    # В этом случае можно попробовать найти его в списке клиентов конкретного инбаунда
                    # Но проще отправить тебе уведомление, что нужно проверить Швецию вручную
                    logger.error(
                        f"⚠️ Критическая рассинхронизация email {email} на сервере {self.server_name}"
                    )
                    raise e
                raise e

        except Exception as e:
            # Отправка ошибки в ТГ (твой текущий код)
            error_msg = (
                f"🚨 <b>Ошибка API на сервере:</b> {self.server_name}\n"
                f"🆔 Inbound ID: {inbound_id}\n"
                f"📧 Email: {email}\n"
                f"⚠️ Error: {str(e)}"
            )
            send_message_to_admin_chanel(error_msg, is_error=True)
            raise

    def get_inbound_config(self, inbound_id: int):
        """Получает конфигурацию инбаунда."""
        try:
            return self.api.inbound.get_by_id(inbound_id)
        except Exception as e:
            logger.error(f"Ошибка получения инбаунда {inbound_id}: {e}")
            return None

    def get_traffic_stats(self, inbound_id: int):
        """Статистика трафика инбаунда."""
        inbound = self.get_inbound_config(inbound_id)
        return inbound.client_stats if inbound else []

    def get_client_stats(self, inbound_id: int):
        """Возвращает список объектов статистики всех клиентов инбаунда."""
        inbound = self.get_inbound_config(inbound_id)
        return inbound.client_stats if inbound and inbound.client_stats else []

    def get_all_clients_stats(self):
        """
        Получает статистику всех клиентов для py3xui версии 0.5.4
        """
        all_stats = []
        try:
            # 1. Получаем все инбаунды (входящие подключения)
            inbounds = self.api.inbound.get_list()

            for ib in inbounds:
                # 2. Если у инбаунда есть статистика клиентов
                if hasattr(ib, "client_stats") and ib.client_stats:
                    all_stats.extend(ib.client_stats)

            return all_stats
        except Exception as e:
            logger.error(
                f"Ошибка получения статистики клиентов на {self.server_name}: {e}"
            )
            return []
