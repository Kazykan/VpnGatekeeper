from doctest import master
import uuid
from django.db import models
from django.utils import timezone


class TelegramUser(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    is_gift = models.BooleanField(
        default=False,
        verbose_name="Подарочная подписка",
        help_text="Если True, пользователь считается родственником/другом, подписка бесплатная",
    )
    # Уникальный токен для получения ссылки подписки
    sub_token = models.UUIDField(default=uuid.uuid4, unique=True)
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

    card_last4 = models.CharField(
        max_length=10, blank=True, null=True
    )  # Опционально: последние 4 цифры карты

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
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        "TelegramUser", on_delete=models.CASCADE, related_name="credentials"
    )
    server = models.ForeignKey(
        "Server", on_delete=models.CASCADE, related_name="credentials"
    )

    # Для статистики
    # Статистика
    up_traff = models.BigIntegerField(default=0, verbose_name="Загружено (байты)")
    down_traff = models.BigIntegerField(default=0, verbose_name="Скачано (байты)")
    total_traff = models.BigIntegerField(default=0, verbose_name="Всего (байты)")
    last_seen = models.DateTimeField(
        null=True, blank=True, verbose_name="Последнее подключение"
    )
    traffic_offset = models.BigIntegerField(default=0)

    # Данные для связи с 3x-ui API
    inbound_id = models.IntegerField(
        null=True, blank=True, help_text="ID инбаунда в панели 3x-ui"
    )
    client_email = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Email клиента в панели (используется как ID для API)",
    )

    # Конфиги
    vless_url = models.TextField(
        blank=True, null=True, verbose_name="Готовая ссылка vless://"
    )

    # Для WireGuard/Amnezia
    wg_conf = models.TextField(blank=True, null=True)
    wg_conf_ip = models.TextField(blank=True, null=True)
    wg_conf_enpoint = models.TextField(
        blank=True, null=True
    )  # Endpoint подключения из конфига
    wg_conf_old_server = models.BooleanField(
        default=False
    )  # флаг, что конфиг с "старого" сервера (для блокировки/разблокировки)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def monthly_usage_bytes(self):
        """Возвращает потребление трафика с начала расчетного периода."""
        usage = self.total_traff - self.traffic_offset
        return usage if usage > 0 else 0

    @property
    def monthly_usage_gb(self):
        return round(self.monthly_usage_bytes / (1024**3), 2)

    @property
    def total_gb(self):
        """Всего накоплено на сервере за все время в ГБ"""
        return round(self.total_traff / (1024**3), 3)

    def __str__(self):
        return f"{self.user.name} @ {self.server.name} (Active: {self.active})"


class Server(models.Model):
    id = models.AutoField(primary_key=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    name = models.CharField(max_length=100, verbose_name="Имя сервера")
    api_url = models.CharField(max_length=255, help_text="Напр: http://1.2.3.4:2053")
    api_username = models.CharField(max_length=100, blank=True, null=True)
    api_password = models.CharField(max_length=255, blank=True, null=True)

    type = models.CharField(
        max_length=20,
        choices=[("amnezia", "AmneziaWG"), ("xray", "3x-ui")],
        default="xray",
    )

    inbound_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID инбаунда для 3x-ui (только для серверов типа xray)",
    )

    base_weight = models.FloatField(
        default=1.0,
        verbose_name="Вес сервера",
        help_text="Используется для балансировки нагрузки",
    )
    max_clients = models.IntegerField(default=1000)

    current_load = models.FloatField(default=0.0, verbose_name="Текущая нагрузка")

    # --- ЛОГИКА РЕЛЕЯ (ПРОКЛАДКИ) ---
    is_relay = models.BooleanField(
        default=False,
        verbose_name="Это транзитный сервер (РФ)",
        help_text="Если включено, трафик будет идти через этот сервер к основному",
    )
    upstream_server = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="relays",
        verbose_name="Целевой сервер (Европа)",
        help_text="Укажите основной сервер, на который этот сервер должен пересылать трафик",
    )

    def __str__(self):
        return f"{self.name} ({'RELAY' if self.is_relay else 'MASTER'})"
