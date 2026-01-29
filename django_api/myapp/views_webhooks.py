# myapp/views_webhooks.py
import json
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
        payment_method = obj.get("payment_method", {})
        saved = payment_method.get("saved", False)
        pm_id = payment_method.get("id")

        # Найти Payment: по provider_payment_id или по metadata.payment_id
        payment = None
        if provider_id:
            payment = Payment.objects.filter(provider_payment_id=provider_id).first()
        if not payment and metadata.get("payment_id"):
            payment = Payment.objects.filter(id=metadata["payment_id"]).first()

        if not payment:
            return Response({"error": "payment not found"}, status=404)

        payment.status = "success"
        payment.raw_payload = json.dumps(request.data)
        payment.save()

        if saved and pm_id:
            user = payment.user
            user.payment_method_id = pm_id
            user.save()

        # Запустить задачу продления подписки (Celery)
        if payment.months > 0:
            extend_subscription_task.delay(
                user_id=payment.user.id, months=payment.months
            )

        # Уведомить пользователя в Telegram

        send_message(
            payment.user.telegram_id, "✅ Оплата прошла. Подписка активирована."
        )
        if saved:
            send_message(
                payment.user.telegram_id,
                "Карта сохранена — автосписания будут работать.",
            )
        else:
            send_message(
                payment.user.telegram_id,
                "Карта не сохранена. Для автосписаний нужно поставить галочку при оплате.",
            )

        return Response({"status": "ok"})
