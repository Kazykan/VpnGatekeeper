import json
from typing import cast
import logging
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from myapp.domain.subscription.load_balancer import get_balanced_credentials
from myapp.domain.subscription.calculations import get_subscription_announce, prepare_subscription_data
from myapp.domain.credentials.selectors import (
    get_active_credentials_for_user,
    get_user_traffic_report,
)
from myapp.domain.credentials.exceptions import NoActiveSubscription
from myapp.domain.credentials.services import generate_new_config_for_user
from myapp.domain.amnezia.parser_conf import generate_simple_configs
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

NEXT_PUBLIC_TELEGRAM_BOT_URL = settings.NEXT_PUBLIC_TELEGRAM_BOT_URL
NEXT_PUBLIC_WEB_APP_URL = settings.NEXT_PUBLIC_WEB_APP_URL
logger = logging.getLogger(__name__)


class TelegramUserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["telegram_id", "invited_by", "sub_token"]

    @action(detail=False, methods=["get"], url_path="full-stats")
    def get_stats_by_tg_id(self, request):
        """
        Получение полной статистики по трафику через telegram_id пользователя.
        Пример: /api/telegram-users/full-stats/?telegram_id=12345
        """
        tg_id = request.query_params.get("telegram_id")
        if not tg_id:
            return Response({"error": "Параметр telegram_id обязателен"}, status=400)

        try:
            user = TelegramUser.objects.get(telegram_id=tg_id)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)

        # Вызываем наш селектор
        report = get_user_traffic_report(user)
        return Response(report)


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


class UnbindCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        telegram_id = request.data.get("telegram_id")

        if not telegram_id:
            return Response({"error": "telegram_id is required"}, status=400)

        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)

            # Самая важная часть для ЮKassa: стираем токен и выключаем флаг
            user.payment_method_id = None
            user.autopay_enabled = False
            user.save()

            return Response(
                {"message": "Карта успешно отвязана", "autopay_enabled": False},
                status=200,
            )

        except TelegramUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class CredentialViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Credential.objects.all()
    serializer_class = CredentialSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["user"]

    @action(detail=False, methods=["get"], url_path="config-by-tg")
    def get_by_tg_id(self, request):
        """
        Возвращает конфиги пользователя для новых серверов (максимум 3).
        """
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response({"error": "Параметр telegram_id обязателен"}, status=400)

        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
        except TelegramUser.DoesNotExist:
            # Пользователя нет вообще
            return Response({"error": "Пользователь не найден"}, status=404)

        # Проверяем наличие новых конфигов
        new_credentials = Credential.objects.filter(
            user__telegram_id=telegram_id, wg_conf_old_server=False
        ).order_by("-id")[:3]

        if new_credentials.exists():
            # Есть новые конфиги → возвращаем их
            response_data = []
            for cred in new_credentials:
                configs = generate_simple_configs(cred)
                if configs:
                    response_data.append(
                        {
                            "credential_id": cred.id,
                            "user_name": user.name,
                            "configs": configs,
                        }
                    )
            return Response(response_data, status=200)

        # Если новых конфигов нет, проверяем, есть ли старые
        old_exists = Credential.objects.filter(
            user__telegram_id=telegram_id, wg_conf_old_server=True
        ).exists()
        if old_exists:
            # Пользователь есть, только старые конфиги → 204 No Content
            return Response(
                {"error": "Пользователь имеет только старые конфиги"}, status=204
            )

        # Пользователь есть, но у него вообще нет конфигов
        return Response({"error": "Конфигов для пользователя не найдено"}, status=404)

    @action(detail=False, methods=["post"], url_path="generate-new-config")
    def generate_new_config(self, request):
        """Генерирует новый конфиг для пользователя и блокирует старый (если он есть)."""
        telegram_id = request.query_params.get("telegram_id")
        if not telegram_id:
            return Response({"error": "telegram_id обязателен"}, status=400)

        try:
            user = TelegramUser.objects.get(telegram_id=telegram_id)
            generate_new_config_for_user(user)
        except TelegramUser.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=404)
        except NoActiveSubscription:
            return Response(
                {"error": "Нет активной подписки"},
                status=403,
            )

        return Response(
            {"message": "Новый конфиг создается. Старый заблокирован"},
            status=200,
        )


class ServerViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class AllAmneziaStatsView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        results = collect_amnezia_stats()
        return Response({"total_servers": len(results), "servers_stats": results})


def user_sub_link_view(request, token):
    """
    Эндпоинт для Happ/Hiddify.
    URL: /sub/<uuid:token>/
    """
    # 1. Selector
    user = get_object_or_404(TelegramUser, sub_token=token)

    # 2. Получаем его ключи СРАЗУ с данными серверов (одним запросом)
    # Это критически важно для производительности!

    credentials_list = list(get_active_credentials_for_user(user))

    # 3. Сортируем с помощью нашего балансировщика
    balanced_creds = get_balanced_credentials(user, credentials_list)

    # 4. Формируем конфиги (теперь они уже в правильном порядке)
    sub_data = prepare_subscription_data(user, balanced_creds)

    # 3. Formating Response
    content = "\n".join(sub_data.links)
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    # конфиг для Happ для настроек обхода ru сайтов они идут на прямую все делается в https://www.happ.su/main/ru/dev-docs/routing
    happ_config = "happ://routing/onadd/eyJOYW1lIjoiIiwiR2xvYmFsUHJveHkiOiJ0cnVlIiwiUm91dGVPcmRlciI6ImJsb2NrLXByb3h5LWRpcmVjdCIsIlJlbW90ZUROU1R5cGUiOiJEb0giLCJSZW1vdGVETlNEb21haW4iOiJodHRwczovL2Nsb3VkZmxhcmUtZG5zLmNvbS9kbnMtcXVlcnkiLCJSZW1vdGVETlNJUCI6IjEuMS4xLjEiLCJEb21lc3RpY0ROU1R5cGUiOiJEb0giLCJEb21lc3RpY0ROU0RvbWFpbiI6Imh0dHBzOi8vZG5zLmdvb2dsZS9kbnMtcXVlcnkiLCJEb21lc3RpY0ROU0lQIjoiOC44LjguOCIsIkdlb2lwdXJsIjoiaHR0cHM6Ly9naXRodWIuY29tL0xveWFsc29sZGllci92MnJheS1ydWxlcy1kYXQvcmVsZWFzZXMvbGF0ZXN0L2Rvd25sb2FkL2dlb2lwLmRhdCIsIkdlb3NpdGV1cmwiOiJodHRwczovL2dpdGh1Yi5jb20vTG95YWxzb2xkaWVyL3YycmF5LXJ1bGVzLWRhdC9yZWxlYXNlcy9sYXRlc3QvZG93bmxvYWQvZ2Vvc2l0ZS5kYXQiLCJMYXN0VXBkYXRlZCI6IjE3NzYyODk3ODYiLCJEbnNIb3N0cyI6eyJjbG91ZGZsYXJlLWRucy5jb20iOiIxLjEuMS4xIiwiZG5zLmdvb2dsZSI6IjguOC44LjgifSwiRGlyZWN0U2l0ZXMiOlsiZ2Vvc2l0ZTpDQVRFR09SWS1SVSJdLCJEaXJlY3RJcCI6WyIxMC4wLjAuMC84IiwiMTcyLjE2LjAuMC8xMiIsIjE5Mi4xNjguMC4wLzE2IiwiMTY5LjI1NC4wLjAvMTYiLCIyMjQuMC4wLjAvNCIsIjI1NS4yNTUuMjU1LjI1NSIsImdlb2lwOlJVIl0sIlByb3h5U2l0ZXMiOltdLCJQcm94eUlwIjpbXSwiQmxvY2tTaXRlcyI6W10sIkJsb2NrSXAiOltdLCJEb21haW5TdHJhdGVneSI6IklQSWZOb25NYXRjaCIsIkZha2VETlMiOiJmYWxzZSIsIlVzZUNodW5rRmlsZXMiOiJ0cnVlIn0"

    # --- ДОБАВЛЯЕМ ОБЪЯВЛЕНИЕ ---
    announce_text = get_subscription_announce(user)
    if announce_text:
        # Важно: Заголовок должен называться 'announce'
        response["announce"] = announce_text
        
    # Заголовок, который Happ распарсит для отображения графиков трафика
    user_info_header = (
        f"upload={sub_data.upload_bytes}; "
        f"download={sub_data.download_bytes}; "
        f"total={sub_data.total_limit_bytes}; "
        f"expire={sub_data.expire_timestamp}"
    )

    # Ссылка на бота/личный кабинет
    response["Profile-Web-Page-Url"] = f"{NEXT_PUBLIC_WEB_APP_URL}/pay/{user.sub_token}/"
    response["support-url"] = NEXT_PUBLIC_TELEGRAM_BOT_URL
    response["Subscription-Userinfo"] = user_info_header
    response["Profile-Title"] = f"Ruf id_{user.telegram_id}"
    # Интервал обновления (в часах)
    response["Profile-Update-Interval"] = "7"
    response["routing"] = happ_config

    return response
