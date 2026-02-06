import base64
import json
import re
import zlib


def select_best_wg_server():
    """Заглушка для выбора сервера (Load Balancer)."""
    return f"wg3.kocherbaev.ru:33042"


def generate_simple_configs(credential):
    """
    Формирует 3 типа подключения:
    1. Main WG (с балансировкой)
    2. Whitelist WG (статика)
    3. VLESS (прямая ссылка)
    """
    if not credential.wg_conf:
        return None

    main_endpoint = select_best_wg_server()
    white_endpoint = "white-list1.kocherbaev.ru:33042"

    # Регулярка для замены Endpoint в текстовом конфиге
    def patch_endpoint(conf_text, new_endpoint):
        return re.sub(
            r"(?i)(Endpoint\s*=\s*)[^ \n\r]+", f"\\1{new_endpoint}", conf_text
        )

    return {
        "main_wg": {
            "title": "Основной сервер (WG)",
            "config_text": patch_endpoint(credential.wg_conf, main_endpoint),
            "endpoint": main_endpoint,
        },
        "whitelist_wg": {
            "title": "Белые списки РФ (WG)",
            "config_text": patch_endpoint(credential.wg_conf, white_endpoint),
            "endpoint": white_endpoint,
        },
        "vless": {
            "title": "Xray VLESS / XHTTP",
            "link": credential.vless_url or "vless://server_not_ready",
        },
    }
