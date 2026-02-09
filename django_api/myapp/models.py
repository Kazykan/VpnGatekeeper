from doctest import master
from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    telegram_id = models.BigIntegerField(unique=True)
    xray_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )
    preshared_key = models.CharField(max_length=255, blank=True, null=True)
    end_date = models.DateField(null=True, blank=True)

    # Флаги бонусов пригласившего храним тут
    invited_bonus_given = models.BooleanField(default=False)
    traffic_bonus_given = models.BooleanField(default=False)

    # telegram_id пригласившего
    invited_by = models.BigIntegerField(blank=True, null=True)
    traffic_on = models.BooleanField(default=False)  # флаг "пошёл трафик"

    # НОВЫЕ ПОЛЯ ДЛЯ АВТОПЛАТЕЖЕЙ
    autopay_enabled = models.BooleanField(
        default=False, verbose_name="Автопродление включено"
    )
    payment_method_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Токен для рекуррентных платежей от провайдера",
    )
    last_payment_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )  # Опционально: статус последней попытки автоплатежа

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        "TelegramUser",  # связь с твоей моделью пользователя
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.IntegerField()  # сумма платежа
    months = models.IntegerField()  # оплаченные месяцы
    provider_payment_id = models.CharField(max_length=255, blank=True, null=True)
    payment_time = models.DateTimeField(default=timezone.now)
    raw_payload = models.TextField(blank=True, null=True)  # сырые данные от провайдера
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
    )
    unique_payload = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"Payment {self.id} by {self.user.telegram_id} ({self.status})"


class Credential(models.Model):
    """Содержит данные для подключения пользователя к серверу
    Если пользователь не оплатил тут мы храним оригинальные данные
    Блокировка по IP выполняется на уровне сервера, а не удалением конфига, чтобы не потерять данные при блокировке из-за неуплаты
    """

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        "TelegramUser", on_delete=models.CASCADE, related_name="credentials"
    )
    wg_conf_enpoint = models.TextField(
        blank=True, null=True
    )  # Endpoint подключения из конфига
    wg_conf = models.TextField(blank=True, null=True)  # готовый .conf
    wg_conf_ip = models.TextField(blank=True, null=True)  # IP из конфига для блокировки
    wg_conf_old_server = models.BooleanField(
        default=False
    )  # флаг, что конфиг с "старого" сервера (для блокировки/разблокировки)
    vless_url = models.TextField(blank=True, null=True)  # ссылка vless://...
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.telegram_id}|{self.user.name}  Credential {self.id} - Active: {self.active} - Old Server: {self.wg_conf_old_server}"


class Server(models.Model):
    id = models.AutoField(primary_key=True)  # Добавьте эту строку
    name = models.CharField(max_length=100)  # удобное имя
    api_url = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20, choices=[("amnezia", "AmneziaWG"), ("xray", "3x-ui")]
    )
    api_username = models.CharField(max_length=100, blank=True, null=True)
    api_password = models.CharField(
        max_length=255, blank=True, null=True
    )  # Желательно зашифровать

    def __str__(self):
        return f"{self.name} ({self.type})"
