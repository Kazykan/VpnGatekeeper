from typing import cast
import logging
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from myapp.tasks.check_payment import check_payment_status
from myapp.domain.amnezia.services import collect_amnezia_stats
from .models import TelegramUser, Payment, Credential, Server
from myapp.domain.infrastructure.yookassa_gateway import create_yookassa_payment
from django.conf import settings
from .serializers import (
    TelegramUserSerializer,
    PaymentSerializer,
    CredentialSerializer,
    ServerSerializer,
)

logger = logging.getLogger(__name__)


class TelegramUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["telegram_id", "invited_by"]


class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


class CreatePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Фильтрация платежей.
        Пример: /api/payments/?id=123
        """
        payment_id = request.query_params.get("id")

        if payment_id:
            payment = Payment.objects.filter(id=payment_id).first()
            if not payment:
                return Response({"error": "payment not found"}, status=404)

            return Response(
                {
                    "id": payment.id,
                    "amount": payment.amount,
                    "status": payment.status,
                    "months": payment.months,
                    "provider_payment_id": payment.provider_payment_id,
                    "payment_time": payment.payment_time,
                    "unique_payload": payment.unique_payload,
                }
            )

        # Если id не передан — можно вернуть список или ошибку
        payments = Payment.objects.all().order_by("-id")
        data = [
            {
                "id": p.id,
                "amount": p.amount,
                "status": p.status,
                "months": p.months,
                "provider_payment_id": p.provider_payment_id,
                "payment_time": p.payment_time,
                "unique_payload": p.unique_payload,
            }
            for p in payments
        ]
        return Response(data)

    def post(self, request):
        telegram_id = request.data.get("telegram_id")
        amount = request.data.get("amount")
        pay_type = request.data.get("type")
        months = int(request.data.get("months", 0))
        unique_payload = request.data.get("unique_payload")

        if not all([telegram_id, amount, pay_type, unique_payload]):
            return Response({"error": "Missing fields"}, status=400)

        # Находим пользователя
        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        # Создаём Payment
        payment = Payment.objects.create(
            user=user,
            amount=int(amount),
            months=months,
            status="pending",
            unique_payload=unique_payload,
        )

        # Создаём платёж в YooKassa
        yk_payment = create_yookassa_payment(
            amount_rub=int(amount),
            description=f"Оплата {months}m {pay_type}",
            save_method=(pay_type == "sub"),
            metadata={"payment_id": payment.id, "unique_payload": unique_payload},
        )

        payment.provider_payment_id = yk_payment.id
        payment.save()

        # Проверка через 10 минут, если вебхук не придёт
        check_payment_status.apply_async((payment.id,), countdown=600)  # type: ignore

        confirmation = yk_payment.confirmation
        if confirmation and hasattr(confirmation, "confirmation_token"):
            token = confirmation.confirmation_token
        else:
            token = None

        return Response(
            {
                "payment_id": payment.id,
                "confirmation_token": token,
            },
            status=201,
        )


class CredentialViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user"]


class ServerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class AllAmneziaStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        results = collect_amnezia_stats()
        return Response({"total_servers": len(results), "servers_stats": results})
