FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости для Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc netcat-openbsd

# Копируем требования и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# Команда запуска (ее переопределит docker-compose, но пусть будет)
CMD ["sh", "-c", "python manage.py migrate && python manage.py createsuperuser --noinput || true && python manage.py runserver 0.0.0.0:8000"]