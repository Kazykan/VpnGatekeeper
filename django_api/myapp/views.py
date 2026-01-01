import re
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .domain.infrastructure.amnezia_gateway import AmneziaGateway
from .models import TelegramUser, Payment, Credential, Server
from .domain.user_service import calculate_new_end_date, calculate_new_end_date_days
from .serializers import (
    TelegramUserSerializer,
    PaymentSerializer,
    CredentialSerializer,
    ServerSerializer,
)


class TelegramUserViewSet(viewsets.ModelViewSet):
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        payment = self.get_object()

        if payment.status == "success":
            user = payment.user
            user.end_date = calculate_new_end_date(
                user.end_date.strftime("%Y-%m-%d") if user.end_date else None, months
            )
            user.save()
            # если есть пригласивший то добавляем ему 20 дней
            if user.invited_by:
                inviter = TelegramUser.objects.filter(
                    telegram_id=user.invited_by
                ).first()
                if inviter:
                    inviter.end_date = calculate_new_end_date_days(
                        (
                            inviter.end_date.strftime("%Y-%m-%d")
                            if inviter.end_date
                            else None
                        ),
                        20,
                    )
                    inviter.save()
        return response


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer

class AllAmneziaStatsView(APIView):
    def get(self, request):
        # 1. Берем все серверы Amnezia из БД
        servers = Server.objects.filter(type='amnezia')
        
        results = []

        for server in servers:
            # 2. Опрашиваем каждый сервер
            gateway = AmneziaGateway(server.api_url)
            stats = gateway.get_stats()
            
            # Формируем структуру ответа для каждого сервера
            results.append({
                "id": server.id,
                "name": server.name,
                "status": "error" if "error" in stats else "ok",
                "data": stats
            })
            
        # 3. Отдаем общий JSON
        return Response({
            "total_servers": len(results),
            "servers_stats": results
        })