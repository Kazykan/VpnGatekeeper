# myapp/tasks/billing.py
from celery import shared_task
from datetime import date, timedelta
from myapp.domain.user_service import calculate_new_end_date
from myapp.models import Payment, TelegramUser, Credential
from myapp.domain.subscription.services import process_autopayment_for_user
from myapp.domain.infrastructure.telegram_gateway import (
    send_message,
    send_message_to_admin_chanel,
)
from django.db.models import Count, Sum
from django.utils import timezone


@shared_task
def daily_billing_check():
    today = date.today()

    # --- 1. БЕСПЛАТНОЕ ПРОДЛЕНИЕ ДЛЯ РОДСТВЕННИКОВ (is_gift=True) ---
    # Продлеваем за 2 дня до окончания, чтобы у них не было даже секундного прерывания
    gift_renewal_target = today + timedelta(days=2)
    gift_users = TelegramUser.objects.filter(is_gift=True, end_date=gift_renewal_target)

    for user in gift_users:
        # Используем вашу функцию для расчета +1 месяц +1 день
        user.end_date = calculate_new_end_date(user.end_date, 1)
        user.save()

        # Запускаем синхронизацию, которая обновит expiry_ts в 3x-ui
        from myapp.tasks.provisioning import sync_vpn_cluster

        sync_vpn_cluster.delay(user.telegram_id)  # type: ignore

        # Уведомляем
        text = (
            f"🎁 <b>Хорошие новости!</b>\n\n"
            f"Руфат продлил вашу подписку еще на месяц.\n"
            f"Доступ активен до: <b>{user.end_date}</b>\n\n"
            f"Пользуйтесь с удовольствием! 🚀"
        )
        send_message(user.telegram_id, text)

    # --- 2. АВТОПЛАТЕЖИ (is_gift=False) ---
    # Уведомление за 3 дня
    notification_target = today + timedelta(days=3)
    users_to_notify = TelegramUser.objects.filter(
        end_date=notification_target, autopay_enabled=True, is_gift=False
    )
    for user in users_to_notify:
        send_message(
            user.telegram_id,
            "🔔 Напоминание: Через 3 дня ваша подписка будет продлена автоматически.",
        )

    # Списание за 2 дня
    charge_target = today + timedelta(days=2)
    users_to_charge = TelegramUser.objects.filter(
        end_date=charge_target,
        autopay_enabled=True,
        payment_method_id__isnull=False,
        is_gift=False,
    )
    for user in users_to_charge:
        from myapp.tasks.billing import run_single_autopay

        run_single_autopay.delay(user.id)  # type: ignore

    # --- 3. УВЕДОМЛЕНИЯ О РУЧНОЙ ОПЛАТЕ ---
    # Для тех, у кого нет автоплатежа и кто не "подарочный"
    for days_left in [10, 5, 2]:
        target_date = today + timedelta(days=days_left)
        users_manual = TelegramUser.objects.filter(
            end_date=target_date, autopay_enabled=False, is_gift=False
        )
        for user in users_manual:
            day_word = "дней" if days_left in [10, 5] else "дня"
            send_message(
                user.telegram_id,
                f"⚠️ Ваша подписка истекает через {days_left} {day_word}.\n"
                f"Пожалуйста, продлите её вручную в боте, чтобы не потерять доступ.",
            )


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
    send_message_to_admin_chanel(msg)


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
    send_message_to_admin_chanel(message)
