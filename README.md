make reset-db

docker exec -it django_api bash
python manage.py createsuperuser

Восстановление backup
Накатываем бэкап (Используем mydb)
Переходим в папку и запускаем импорт. Обрати внимание, я подставил user и mydb из твоего последнего сообщения:

Bash
cd /root/VpnGatekeeper/backups_data/

# Импорт
cat backup_2026-02-14_23-05.sql | docker exec -i postgres_db psql -U user -d mydb