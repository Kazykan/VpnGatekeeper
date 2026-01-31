# myapp/tasks/billing.py
from celery import shared_task
from datetime import date, timedelta
from backend import settings
from myapp.models import Payment, TelegramUser
from myapp.domain.subscription.services import process_autopayment_for_user
from myapp.domain.infrastructure.telegram_gateway import send_message
from django.db.models import Count, Sum
from django.utils import timezone


@shared_task
def daily_billing_check():
    today = date.today()

    # 1. Уведомление ЗА 3 ДНЯ
    # Если end_date = 2026-02-03, а сегодня 2026-01-31, то разница 3 дня.
    notification_target = today + timedelta(days=3)
    users_to_notify = TelegramUser.objects.filter(
        end_date=notification_target, autopay_enabled=True
    )

    for user in users_to_notify:
        send_message(
            user.telegram_id,
            "🔔 Напоминание: Через 2 дня ваша подписка будет продлена автоматически.",
        )

    # 2. Списание ЗА 2 ДНЯ
    charge_target = today + timedelta(days=2)
    users_to_charge = TelegramUser.objects.filter(
        end_date=charge_target, autopay_enabled=True, payment_method_id__isnull=False
    )

    for user in users_to_charge:
        # Запускаем процесс списания асинхронно для каждого пользователя
        # Чтобы ошибка у одного не остановила очередь для остальных
        run_single_autopay.delay(user.id)  # type: ignore


@shared_task
def run_single_autopay(user_id):
    """Обертка для запуска процесса списания в фоне"""
    process_autopayment_for_user(user_id)


@shared_task
def send_daily_admin_stats():
    yesterday = timezone.now() - timedelta(days=1)

    # Собираем данные
    stats = (
        Payment.objects.filter(payment_time__gte=yesterday)
        .values("status")
        .annotate(count=Count("id"), total=Sum("amount"))
    )

    # Формируем красивое сообщение
    msg = "📊 **Статистика платежей за 24ч:**\n\n"
    grand_total = 0

    for entry in stats:
        status = entry["status"]
        count = entry["count"]
        total = entry["total"] or 0

        emoji = "✅" if status == "success" else "⏳" if status == "pending" else "❌"
        msg += f"{emoji} {status.capitalize()}: {count} шт. ({total} руб.)\n"

        if status == "success":
            grand_total = total

    msg += f"\n💰 **Итого выручка:** {grand_total} руб."

    # Отправляем админу
    send_message(settings.ADMIN_TELEGRAM_ID, msg)


def notify_admin_about_new_client(user_pk, payment_pk):
    """
    Отправляет уведомление админу.
    Используем первичные ключи (pk), чтобы достать свежие данные.
    """
    try:
        user = TelegramUser.objects.get(pk=user_pk)
        payment = Payment.objects.get(pk=payment_pk)
    except (TelegramUser.DoesNotExist, Payment.DoesNotExist):
        return

    # Ищем пригласившего (так как invited_by это просто число, а не ForeignKey)
    inviter_text = "Органически"
    if user.invited_by:
        inviter = TelegramUser.objects.filter(telegram_id=user.invited_by).first()
        if inviter:
            inviter_text = f"[{inviter.name}](tg://user?id={inviter.telegram_id})"
        else:
            inviter_text = f"ID: `{user.invited_by}` (не найден в БД)"

    # Формируем красивое сообщение
    message = (
        "🚀 **Новый платный пользователь!**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {user.name}\n"
        f"🆔 **TG ID:** `{user.telegram_id}`\n"
        f"💰 **Сумма:** {payment.amount} руб.\n"
        f"📅 **Срок:** {payment.months} мес.\n"
        f"🔗 **Приглашен:** {inviter_text}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 **Автоплатеж:** {'✅ Включен' if user.autopay_enabled else '❌ Выключен'}"
    )

    # Отправляем админу
    send_message(settings.ADMIN_TELEGRAM_ID, message)
