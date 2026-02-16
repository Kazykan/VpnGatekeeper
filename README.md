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

Настройка nginx для работы vpnkeeper

```bash
vim /etc/nginx/sites-available/my_project.conf
```

```nginx
# --- СЕКЦИЯ NEXT.JS MINIAPP ---
server {
    listen 80;
    server_name portal.domen.ru;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# --- СЕКЦИЯ DJANGO API ---
server {
    listen 80;
    server_name core-api.domen.ru;

    # Проброс статики
    location /static/ {
        alias /var/lib/docker/volumes/vpngatekeeper_django_static/_data/;
        autoindex on;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Проброс медиа
    location /media/ {
        alias /var/lib/docker/volumes/vpngatekeeper_django_media/_data/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
vim setup-nginx.sh
```

```bash
#!/bin/bash

# 1. Обновляем репозитории и ставим Nginx + Certbot
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# 2. Создаем символическую ссылку (если файл уже лежит в sites-available)
# Замените 'my_project.conf' на реальное имя вашего файла, если оно другое
sudo ln -sf /etc/nginx/sites-available/my_project.conf /etc/nginx/sites-enabled/

# 3. Удаляем дефолтный конфиг, чтобы он не мешал (необязательно, но полезно)
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Проверяем конфиг на ошибки
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Nginx config is OK. Reloading..."
    sudo systemctl reload nginx
else
    echo "Nginx config has errors. Please check the file."
    exit 1
fi

# 5. Запускаем Certbot для получения сертификатов
# Он сам найдет server_names в конфиге и предложит сделать редирект
sudo certbot --nginx -d portal.domen.ru -d core-api.domen.ru
```

запускаем

```bash
chmod +x setup-nginx.sh
./setup-nginx.sh
```

собираем статику

```bash
docker compose exec django python manage.py collectstatic --no-input
```

даем права на нее nginx

```bash
# Даем права на чтение содержимого вольюмов для Nginx
sudo chown -R 755 /var/lib/docker/volumes/vpngatekeeper_django_static/_data/
sudo chown -R 755 /var/lib/docker/volumes/vpngatekeeper_django_media/_data/
chmod +x /var/lib/docker
chmod +x /var/lib/docker/volumes
chmod +x /var/lib/docker/volumes/vpngatekeeper_django_static
```

создаем БД и суперпользователя

```bash
docker exec -it django_api python manage.py migrate docker exec -it django_api python manage.py createsuperuser
```


меняем адрес для yookassa https://yookassa.ru/my/merchant/integration/http-notifications
https://core-api.domain.ru/api/yookassa/webhook/
Адрес для получения уведомлений