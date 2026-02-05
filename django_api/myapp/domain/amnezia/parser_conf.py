import base64
import json
import re
import zlib


def encode_amnezia_standard(data_dict):
    """
    Кодирование по стандарту Amnezia (zlib + header + base64).
    Используется для того, чтобы ссылки гарантированно открывались.
    """
    json_str = json.dumps(data_dict, indent=4).encode()
    compressed = zlib.compress(json_str)

    # 4-байтовый заголовок с длиной данных
    header = len(json_str).to_bytes(4, byteorder="big")

    # URL-safe кодирование без лишних знаков '=' в конце
    encoded = base64.urlsafe_b64encode(header + compressed).decode().rstrip("=")
    return encoded


def get_amnezia_settings(conf_text, new_endpoint=None):
    """Парсит текст конфига AmneziaWG в словарь."""
    if not conf_text:
        return {}

    amnezia_settings = {}
    pattern = re.compile(r"^\s*([\w\d]+)\s*=\s*(.*)$", re.MULTILINE)
    matches = pattern.findall(conf_text)

    # Поля, которые Amnezia ожидает видеть как числа
    numeric_fields = [
        "Jc",
        "Jmin",
        "Jmax",
        "S1",
        "S2",
        "S3",
        "S4",
        "port",
        "PersistentKeepalive",
    ]

    for key, value in matches:
        key = key.strip()
        value = value.strip()

        if key == "Endpoint" and new_endpoint:
            amnezia_settings[key] = new_endpoint
        elif key in numeric_fields:
            try:
                amnezia_settings[key] = int(value)
            except ValueError:
                amnezia_settings[key] = value
        else:
            amnezia_settings[key] = value

    return amnezia_settings


def generate_vpn_config_links(credential):
    """Генерация ссылок для ответа API."""
    if not credential.wg_conf:
        return None

    # Настройки эндпоинтов (можно заменить на данные из credential.server.address)
    main_endpoint = "wg3.kocherbaev.ru:33042"
    white_endpoint = "gw_white1.kocherbaev.ru:33042"

    wg_settings_main = get_amnezia_settings(
        credential.wg_conf, new_endpoint=main_endpoint
    )
    wg_settings_white = get_amnezia_settings(
        credential.wg_conf, new_endpoint=white_endpoint
    )

    # 1. Структура для всей пачки (amnezia://)
    amnezia_json = {
        "containers": [
            {
                "name": "Rufat Proxy (Main)",
                "container": "amnezia-wg",
                "hostname": main_endpoint.split(":")[0],
                "port": int(main_endpoint.split(":")[1]),
                "settings": wg_settings_main,
            },
            {
                "name": "Белые списки (РФ)",
                "container": "amnezia-wg",
                "hostname": white_endpoint.split(":")[0],
                "port": int(white_endpoint.split(":")[1]),
                "settings": wg_settings_white,
            },
            {
                "name": "Xray VLESS",
                "container": "xray",
                "hostname": main_endpoint.split(":")[0],
                "port": 443,
                "settings": {"vless_url": credential.vless_url or ""},
            },
        ]
    }

    # 2. Структура для одиночного конфига (vpn://) — берем Main
    ios_json = amnezia_json["containers"][0]

    # Кодируем обе ссылки через "умный" упаковщик со сжатием
    # (Amnezia отлично понимает сжатый формат и в ссылках amnezia://)
    amnezia_payload = encode_amnezia_standard(amnezia_json)
    ios_payload = encode_amnezia_standard(ios_json)

    return {
        "amnezia_url": f"amnezia://{amnezia_payload}",
        "default_vpn_url": f"vpn://{ios_payload}",
        "vless_raw": credential.vless_url,
        "raw_wg_conf": credential.wg_conf,
    }
