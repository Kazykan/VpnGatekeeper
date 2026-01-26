from typing import cast
import logging
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated

from myapp.domain.subscription.services import extend_subscription_task
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

    def post(self, request, *args, **kwargs):
        telegram_id = request.data.get("telegram_id")
        amount = request.data.get("amount")
        pay_type = request.data.get("type")
        months = int(request.data.get("months", 0))
        unique_payload = request.data.get("unique_payload")

        if not all([telegram_id, amount, pay_type, unique_payload]):
            return Response({"error": "Missing fields"}, status=400)

        # Валидация тарифа по ENV

        # tariff = settings.TARIFFS_BY_PRICE.get(int(amount))
        # if not tariff or tariff["type"] != pay_type or tariff["period"] != f"{months}m":
        #     return Response({"error": "Invalid tariff"}, status=400)

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

        return Response(
            {
                "payment_id": payment.id,
                "confirmation_token": yk_payment.confirmation.confirmation_token,
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
