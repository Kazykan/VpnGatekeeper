from datetime import timedelta
import os
from pathlib import Path
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-b*#3l)g*r1gf6s1ahqdnnlfpo!t^*h^^i)(q+o51ax_=_f4oql"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "django",  # ← важно
    "django:8000",  # ← можно, но не обязательно
    "*",
    "djangoapi.kocherbaev.ru",
    "test-djangoapi.kocherbaev.ru",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "myapp",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Должно быть в самом верху!
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "django_db"),
        "USER": os.environ.get("POSTGRES_USER", "user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "pass"),
        "HOST": os.environ.get(
            "DB_HOST", "db"
        ),  # 'db' — это имя сервиса в docker-compose
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")
ADMIN_CHANNEL_ID = os.getenv("ADMIN_CHANNEL_ID")
NEXT_PUBLIC_TELEGRAM_BOT_URL = os.getenv("NEXT_PUBLIC_TELEGRAM_BOT_URL")

CELERY_BROKER_URL = "redis://redis:6379/0"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",  # Используем 1-ю базу (0-я обычно для Celery)
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

CELERY_BEAT_SCHEDULE = {
    "check-subscriptions-every-morning": {
        "task": "myapp.tasks.billing.daily_billing_check",
        "schedule": crontab(hour=9, minute=0),  # Каждый день в 9 утра
    },
    # Добавляем обновление трафика
    "update-traffic-stats-every-15-min": {
        "task": "myapp.tasks.stats.update_all_servers_traffic",
        # "schedule": crontab(minute="*"),  # Раз в минут
        "schedule": crontab(minute="*/15"),  # Раз в 15 минут
    },
    "nightly-db-backup": {
        "task": "myapp.tasks.backup.create_db_backup",
        "schedule": crontab(hour=23, minute=42),  # В 3 часа ночи
    },
}

# Получаем строку из переменной окружения
cors_raw = os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "")

# Парсим: убираем пробелы и создаем список, если строка не пустая
if cors_raw:
    CORS_ALLOWED_ORIGINS = [
        origin.strip() for origin in cors_raw.split(",") if origin.strip()
    ]
else:
    CORS_ALLOWED_ORIGINS = []

# Не забудь про заголовки, иначе фронтенд не увидит трафик!
CORS_EXPOSE_HEADERS = [
    "Subscription-Userinfo",
    "Profile-Title",
    "Profile-Update-Interval",
]
