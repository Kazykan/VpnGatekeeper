# myapp/views_webhooks.py
import json
from myapp.tasks.billing import notify_admin_about_new_client
from myapp.domain.subscription.services import extend_subscription_task
from myapp.models import Payment
from rest_framework.views import APIView
from rest_framework.response import Response
from myapp.domain.infrastructure.telegram_gateway import send_message


class YooKassaWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        event = request.data.get("event")
        obj = request.data.get("object", {})

        if event != "payment.succeeded":
            return Response({"status": "ignored"})

        provider_id = obj.get("id")
        metadata = obj.get("metadata", {})
        is_auto_charge = metadata.get("is_auto_charge", False)  # Получаем флаг

        payment_method = obj.get("payment_method", {})
        saved = payment_method.get("saved", False)
        pm_id = payment_method.get("id")

        # Поиск платежа
        payment = None
        if provider_id:
            payment = Payment.objects.filter(provider_payment_id=provider_id).first()
        if not payment and metadata.get("payment_id"):
            payment = Payment.objects.filter(id=metadata["payment_id"]).first()

        if not payment:
            return Response({"error": "payment not found"}, status=404)

        # Обновляем статус платежа
        payment.status = "success"
        payment.raw_payload = json.dumps(request.data)
        payment.save()

        user = payment.user

        # Считаем количество успешных платежей пользователя
        # Если это ПЕРВЫЙ успех — значит перед нами новый клиент
        success_count = Payment.objects.filter(user=user, status="success").count()
        if success_count == 1:
            notify_admin_about_new_client(user.id, payment.id)

        # ЛОГИКА АВТОПЛАТЕЖЕЙ
        if is_auto_charge:
            # Если это автосписание, просто уведомляем об успехе продления
            send_message(
                user.telegram_id, "🔄 Подписка успешно продлена автоматически."
            )
        else:
            # Если это РУЧНОЙ платеж
            if user.autopay_enabled:
                user.autopay_enabled = False
                # user.payment_method_id = None # Оставляем ID, чтобы юзер мог включить обратно без ввода карты
                user.save()
                send_message(
                    user.telegram_id, "ℹ️ Вы оплатили вручную. Автосписание отключено."
                )

            # Стандартные уведомления для ручной оплаты
            send_message(user.telegram_id, "✅ Оплата прошла. Подписка активирована.")
            if saved and pm_id:
                user.payment_method_id = pm_id
                user.autopay_enabled = True  # Если поставил галочку — включаем
                user.save()
                send_message(
                    user.telegram_id, "💳 Карта сохранена — автопродление включено."
                )
            elif not saved:
                send_message(
                    user.telegram_id,
                    "⚠️ Карта не сохранена. Для автосписаний нужно выбрать 'Сохранить карту'.",
                )

        # Запустить задачу продления в любом случае
        if payment.months > 0:
            extend_subscription_task.delay(user_id=user.id, months=payment.months)  # type: ignore

        return Response({"status": "ok"})
