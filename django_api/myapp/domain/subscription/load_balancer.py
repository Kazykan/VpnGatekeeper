# myapp/domain/subscription/load_balancer.py
from typing import Iterable, List
from myapp.models import Credential, TelegramUser


def get_balanced_credentials(
    user: TelegramUser, credentials: Iterable[Credential]
) -> List[Credential]:
    """
    Принимает список credentials и сортирует их так, чтобы:
    1. Самые свободные серверы были сверху (server.current_load).
    2. Порядок был стабильным для конкретного юзера (user_seed).
    """

    def sort_key(cred):
        server = cred.server
        # 1. Основной вес — это нагрузка (от 0.0 до 1.0)
        load = getattr(server, "current_load", 0.0)

        # 2. "Персональная соль" (от 0.000 до 0.099)
        # Делим на 1000, чтобы соль влияла на сортировку только если нагрузки почти равны.
        # Если на одном сервере 10% (0.1), а на другом 25% (0.25),
        # соль не перебьет разницу, и более свободный сервер всё равно будет выше.
        user_seed = (hash(f"{user.id}-{server.id}") % 100) / 1000.0

        return load + user_seed

    # Превращаем QuerySet в список и сортируем.
    # ВАЖНО: credentials должен быть получен с .select_related('server')
    return sorted(list(credentials), key=sort_key)
