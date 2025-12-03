from django.db import models
from django.utils import timezone


# Create your models here.
class TelegramUser(models.Model):
    name = models.CharField(max_length=100)
    telegram_id = models.BigIntegerField(unique=True)
    xray_id = models.CharField(max_length=100, unique=True)
    preshared_key = models.CharField(max_length=255, blank=True, null=True)
    end_date = models.DateTimeField(default=timezone.now)
    invited_by = models.BigIntegerField(
        blank=True, null=True
    )  # telegram_id пригласившего
    traffic_on = models.BooleanField(default=False)  # флаг "пошёл трафик"

    def __str__(self):
        return f"{self.name} ({self.telegram_id})"


class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
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
        return f"Payment {self.payment_id} by {self.user.telegram_id} ({self.status})"


class Credential(models.Model):
    user = models.ForeignKey(
        "TelegramUser", on_delete=models.CASCADE, related_name="credentials"
    )
    server = models.ForeignKey(
        "Server", on_delete=models.CASCADE, related_name="credentials"
    )
    wg_conf = models.TextField(blank=True, null=True)  # готовый .conf
    vless_url = models.TextField(blank=True, null=True)  # ссылка vless://...
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)


class Server(models.Model):
    name = models.CharField(max_length=100)  # удобное имя
    host = models.CharField(max_length=255)  # IP или домен
    api_url = models.CharField(max_length=255, blank=True, null=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(
        max_length=20, choices=[("amnezia", "AmneziaWG"), ("xray", "3x-ui")]
    )

    def __str__(self):
        return f"{self.name} ({self.type})"
