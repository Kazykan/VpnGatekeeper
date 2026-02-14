import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")

# Используем строку для конфига, чтобы Celery не грузил Django слишком рано
app.config_from_object("django.conf:settings", namespace="CELERY")

# Явно указываем модули для регистрации задач.
# Это заменяет autodiscover и работает на 100% стабильнее
app.conf.imports = [
    "myapp.tasks.stats",
    "myapp.tasks.billing",
    "myapp.tasks.check_payment",
    "myapp.tasks.provisioning",
]

app.autodiscover_tasks()
