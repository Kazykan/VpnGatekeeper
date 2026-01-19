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

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        payment = cast(Payment, self.get_object())

        payment.refresh_from_db()  # ← гарантированно обновлённые данные

        print(f"DEBUG: Status in DB is '{payment.status}'", flush=True)

        if payment.status == "success":
            print("DEBUG: Condition met! Sending task...", flush=True)
            extend_subscription_task(user_id=payment.user.id, months=payment.months)
        return response


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
