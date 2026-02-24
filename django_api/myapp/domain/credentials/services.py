# myapp/domain/credentials/services.py
from datetime import date, timedelta
import logging
from django.utils import timezone
from urllib.parse import urlencode, urlparse
from myapp.models import TelegramUser, Credential, Server
from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.infrastructure.amnezia_gateway import AmneziaGateway
import uuid
from datetime import datetime
from myapp.models import Server, Credential, TelegramUser
from myapp.domain.infrastructure.xray_gateway import XrayGateway

logger = logging.getLogger(__name__)


def generate_new_config_for_user(user: TelegramUser) -> None:
    """
    Бизнес-сценарий:
    - проверить подписку
    - заблокировать старые конфиги
    - создать новый конфиг
    """
    from myapp.tasks.provisioning import sync_vpn_cluster

    # 1️⃣ Проверка подписки
    if not user.end_date or user.end_date < date.today():
        raise NoActiveSubscription

    # 2️⃣ Блокировка старых конфигов
    old_server = Server.objects.filter(
        type="amnezia", name__icontains="Old_server"
    ).first()

    old_credentials = Credential.objects.filter(
        user=user,
        wg_conf_old_server=True,
        active=True,
    )

    if old_server and old_credentials.exists():
        gateway = AmneziaGateway(
            api_url=old_server.api_url,
            username=old_server.api_username,
            password=old_server.api_password,
        )

        for cred in old_credentials:
            if cred.wg_conf_ip:
                gateway.block_ip(cred.wg_conf_ip)
            cred.active = False
            cred.save(update_fields=["active"])

    # 3️⃣ Создание нового конфига (через cluster sync)
    sync_vpn_cluster.delay(user.telegram_id)  # type: ignore


def sync_xray_user_credentials(user: TelegramUser):
    """Бизнес-логика синхронизации Xray."""
    if not user.xray_id:
        user.xray_id = str(uuid.uuid4())
        user.save()

    client_email = f"tg_{user.telegram_id}"
    expiry_ts = 0
    if user.end_date:
        expiry_ts = int(
            datetime.combine(user.end_date, datetime.min.time()).timestamp() * 1000
        )

    servers = Server.objects.filter(type="xray", is_active=True)
    if not servers.exists():
        logger.error("❌ Синхронизация прервана: в БД нет серверов типа xray")
        return

    for server in servers:
        try:
            gateway = XrayGateway(
                server.api_url, server.api_username, server.api_password, server.name
            )
            inbound_id = server.inbound_id or 1

            # 1. Синхронизируем в 3x-ui
            gateway.upsert_client(inbound_id, user.xray_id, client_email, expiry_ts)

            # 2. Формируем ссылку
            inbound = gateway.get_inbound_config(inbound_id)
            if not inbound:
                logger.error(
                    f"❌ Не удалось получить конфиг инбаунда {inbound_id} для сервера {server.name}"
                )
                continue

            host = _get_target_host(server)
            vless_url = _build_vless_url(inbound, user.xray_id, host, server.name)

            # 3. Сохраняем в БД
            Credential.objects.update_or_create(
                user=user,
                server=server,
                defaults={
                    "client_email": client_email,
                    "vless_url": vless_url,
                    "active": True,
                },
            )
            logger.info(
                f"✅ Credential успешно создан/обновлен для {user.telegram_id} на сервере {server.name}"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке сервера {server.name}: {str(e)}")
            continue


def _get_target_host(server: Server) -> str:
    """Определяет IP/Домен для подключения клиента."""
    # Пытаемся найти релей, привязанный к этому серверу
    relay = Server.objects.filter(upstream_server=server, is_relay=True).first()

    # Если это релей, берем его адрес, иначе адрес самого сервера
    url_to_parse = relay.api_url if relay else server.api_url

    # Исправляем url для urlparse (нужен протокол)
    if "://" not in url_to_parse:
        url_to_parse = f"http://{url_to_parse}"

    parsed = urlparse(url_to_parse)
    return parsed.hostname or parsed.netloc.split(":")[0] or url_to_parse


def _build_vless_url(inbound, user_uuid: str, host: str, server_name: str) -> str:
    """
    Финальная версия: динамически строит VLESS URL на основе данных из логов.
    """
    stream = inbound.stream_settings

    # Извлекаем транспорт и безопасность из атрибутов объекта
    network = getattr(stream, "network", "tcp")
    security = getattr(stream, "security", "none")

    # Собираем параметры для строки запроса
    params = {
        "type": network,
        "security": security,
    }

    # Если безопасность REALITY (как в логах)
    if security == "reality":
        rs = getattr(stream, "reality_settings", {})
        # Извлекаем вложенный словарь settings
        inner_settings = rs.get("settings", {})

        params["pbk"] = inner_settings.get("publicKey", "")
        params["fp"] = inner_settings.get("fingerprint", "chrome")
        params["sni"] = rs.get("serverNames", [""])[0]
        params["sid"] = rs.get("shortIds", [""])[0]
        params["spx"] = inner_settings.get("spiderX", "/")

    # Если транспорт xHTTP
    if network == "xhttp":
        # Поскольку в логах xhttp_settings не видно, используем стандарт 3X-UI
        # Обычно это /xh/ или путь из конфига
        params["path"] = "/xh/"
        params["mode"] = "auto"

    # Кодируем параметры в строку (key=value&key2=value2)
    query_string = urlencode(params)

    # Порт берем из объекта инбаунда
    port = getattr(inbound, "port", 443)

    return f"vless://{user_uuid}@{host}:{port}?{query_string}#{server_name}"


def update_credential_statistics(credential: Credential, up: int, down: int):
    """
    Бизнес-логика обновления статистики с защитой от сброса сервера.
    """

    old_total = credential.total_traff or 0
    current_total = up + down

    # Проверка на сброс счетчиков на сервере
    if current_total < old_total:
        credential.total_traff = 0
        credential.up_traff = 0
        credential.down_traff = 0
        credential.traffic_offset = 0
        old_total = 0  # важно обновить old_total

    # Если трафик увеличился — фиксируем активность
    if current_total > old_total:
        credential.last_seen = timezone.now()

    # Обновляем значения
    credential.up_traff = up
    credential.down_traff = down
    credential.total_traff = current_total

    credential.save()


def reset_monthly_traffic_offset():
    """Устанавливает текущий трафик как точку отсчета для нового месяца."""
    for cred in Credential.objects.filter(active=True):
        cred.traffic_offset = cred.total_traff
        cred.save()


def sync_server_traffic(server: Server):
    """Синхронизирует статистику всех пользователей конкретного сервера"""
    gateway = XrayGateway(
        server.api_url, server.api_username, server.api_password, server.name
    )

    # Получаем данные из панели
    stats_from_panel = gateway.get_all_clients_stats()

    active_count = 0 
    now = timezone.now()
    activity_threshold = now - timedelta(minutes=20)

    logger.info(f"--- Syncing server {server.name} ---")
    logger.info(f"Found {len(stats_from_panel)} client stats in 3x-ui")

    for stat in stats_from_panel:
        # Ищем соответствующий Credential в нашей БД по email
        credential = Credential.objects.filter(
            server=server, client_email=stat.email, active=True
        ).first()
        logger.debug(f"Processing client {stat.email}: UP {stat.up}, DOWN {stat.down}")

        if credential:
            # Используем вашу логику обновления (с защитой от сброса)
            update_credential_statistics(
                credential=credential, up=stat.up, down=stat.down
            )
            # Считаем пользователя активным, если он "светился" в базе недавно
            # (last_seen обновился внутри update_credential_statistics)
            if credential.last_seen and credential.last_seen >= activity_threshold:
                active_count += 1
                
    # Считаем нагрузку (с учетом твоих полей веса и лимитов)
    # Формула: (активные / лимит) / вес
    # Если вес 2.0, нагрузка будет в 2 раза меньше (сервер "сильнее")
    load = (active_count / server.max_clients) / server.base_weight
    
    server.current_load = round(min(load, 1.0), 3)
    server.save(update_fields=['current_load'])