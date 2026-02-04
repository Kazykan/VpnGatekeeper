import base64
import json
import re
from django.http import JsonResponse
from django.conf import settings


def parse_wg_conf(conf_text):
    """Парсит текст конфига в словарь для JSON"""
    data = {}
    # Извлекаем значения через регулярки
    patterns = {
        "Address": r"Address\s*=\s*(.*)",
        "PrivateKey": r"PrivateKey\s*=\s*(.*)",
        "PublicKey": r"PublicKey\s*=\s*(.*)",
        "PresharedKey": r"PresharedKey\s*=\s*(.*)",
        "Endpoint": r"Endpoint\s*=\s*(.*)",
        "Jc": r"Jc\s*=\s*(\d+)",
        "Jmin": r"Jmin\s*=\s*(\d+)",
        "Jmax": r"Jmax\s*=\s*(\d+)",
        "S1": r"S1\s*=\s*(\d+)",
        "S2": r"S2\s*=\s*(\d+)",
        "H1": r"H1\s*=\s*(.*)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, conf_text)
        if match:
            data[key] = match.group(1).strip()
    return data


def get_vpn_configs(request, user_id):
    # 1. Заглушка Load Balancer (выбираем случайный эндпоинт)
    # В будущем тут: Server.objects.order_by('current_users').first()
    main_endpoint = "wg1.kocherbaev.ru:33042"
    white_endpoint = "gw_white1.kocherbaev.ru:33042"  # РФ Шлюз

    # 2. Получаем Credential из БД
    # credential = Credential.objects.get(user__id=user_id)
    # wg_data = parse_wg_conf(credential.wg_conf)

    # Для примера имитируем данные AmneziaWG
    wg_data = {
        "Address": "10.8.1.10/32",
        "PrivateKey": "base64...",
        "PublicKey": "base64...",
        "Jc": 4,
    }

    # 3. Формируем структуру для Amnezia (Android/PC)
    # Она поддерживает список контейнеров
    amnezia_json = {
        "containers": [
            {
                "name": "Rufat Proxy (Main)",
                "container": "amnezia-wg",
                "hostname": main_endpoint.split(":")[0],
                "port": int(main_endpoint.split(":")[1]),
                "settings": wg_data,
            },
            {
                "name": "Белые списки (РФ)",
                "container": "amnezia-wg",
                "hostname": white_endpoint.split(":")[0],
                "port": int(white_endpoint.split(":")[1]),
                "settings": wg_data,  # Те же ключи, другой хост
            },
        ]
    }

    # 4. Кодируем в Base64
    amnezia_b64 = base64.b64encode(json.dumps(amnezia_json).encode()).decode()

    # Ссылка для iOS (DefaultVPN обычно ждет один конфиг в JSON)
    ios_json = amnezia_json["containers"][0]
    ios_b64 = base64.b64encode(json.dumps(ios_json).encode()).decode()

    return JsonResponse(
        {
            "amnezia_url": f"amnezia://{amnezia_b64}",
            "default_vpn_url": f"vpn://{ios_b64}",
            "raw_conf": "...",  # на случай ручной настройки
        }
    )
