import sqlite3
from datetime import datetime
from django.db import transaction
from myapp.models import TelegramUser, Server, Credential


def import_from_old_db(active_after_date, db_path="/app/database.db"):
    """
    Вынесенная логика импорта пользователей и конфигов из старой SQLite БД.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Извлекаем данные пользователя и все параметры конфига
    cursor.execute(
        """
        SELECT
            u.telegram_id, u.name, u.end_date,
            c.address, c.private_key, c.dns, c.public_key,
            c.endpoint, c.preshared_key, c.persistent_keepalive,
            c.jc, c.jmin, c.jmax, c.s1, c.s2, c.h1, c.h2, c.h3, c.h4
        FROM users u
        LEFT JOIN configs c ON c.user_id = u.user_id
        WHERE u.is_unlimited = 0
        """
    )

    try:
        old_server = Server.objects.get(name__icontains="Old_server")
    except Server.DoesNotExist:
        old_server = None

    imported_count = 0
    rows = cursor.fetchall()

    # Используем транзакцию для ускорения записи в БД
    with transaction.atomic():
        for row in rows:
            (
                tid,
                name,
                end_date_str,
                addr,
                priv,
                dns,
                pub,
                endp,
                psk,
                keep,
                jc,
                jmin,
                jmax,
                s1,
                s2,
                h1,
                h2,
                h3,
                h4,
            ) = row

            # 1. Обработка даты
            current_end_date = None
            if end_date_str:
                try:
                    current_end_date = datetime.strptime(
                        end_date_str, "%Y-%m-%d"
                    ).date()
                except (ValueError, TypeError):
                    current_end_date = None

            is_active = current_end_date and current_end_date >= active_after_date
            target_date = current_end_date if is_active else None

            # 2. Создаем/обновляем пользователя
            user, _ = TelegramUser.objects.update_or_create(
                telegram_id=int(tid),
                defaults={
                    "name": name or f"user_{tid}",
                    "end_date": target_date,
                },
            )

            # 3. Сборка текста конфига (WireGuard + Amnezia)
            if priv and pub:
                config_lines = [
                    "[Interface]",
                    f"PrivateKey = {priv}",
                    f"Address = {addr}",
                    f"DNS = {dns or '1.1.1.1'}",
                ]

                if jc is not None:
                    config_lines.extend(
                        [
                            f"Jc = {jc}",
                            f"Jmin = {jmin}",
                            f"Jmax = {jmax}",
                            f"S1 = {s1}",
                            f"S2 = {s2}",
                            f"H1 = {h1}",
                            f"H2 = {h2}",
                            f"H3 = {h3}",
                            f"H4 = {h4}",
                        ]
                    )

                config_lines.append("\n[Peer]")
                config_lines.append(f"PublicKey = {pub}")
                if psk:
                    config_lines.append(f"PresharedKey = {psk}")
                if endp:
                    config_lines.append(f"Endpoint = {endp}")
                config_lines.append("AllowedIPs = 0.0.0.0/0")
                if keep:
                    config_lines.append(f"PersistentKeepalive = {keep}")

                full_config_text = "\n".join(config_lines)

                # 4. Привязка к серверу (только для активных)
                if is_active and old_server:
                    Credential.objects.update_or_create(
                        user=user,
                        server=old_server,
                        defaults={
                            "wg_conf": full_config_text,
                            "wg_conf_ip": addr,
                            "wg_conf_old_server": True,
                            "active": True,
                        },
                    )

            imported_count += 1

    conn.close()
    return imported_count
