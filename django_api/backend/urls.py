from myapp.views_webhooks import YooKassaWebhookView
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from myapp.views import (
    AllAmneziaStatsView,
    CreatePaymentView,
    CredentialViewSet,
    PaymentViewSet,
    ServerViewSet,
    TelegramUserViewSet,
)

router = DefaultRouter()
router.register(r"users", TelegramUserViewSet)
router.register(r"payments", PaymentViewSet)
router.register(r"credentials", CredentialViewSet)
router.register(r"servers", ServerViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/servers/amnezia-stats/",
        AllAmneziaStatsView.as_view(),
        name="all-amnezia-stats",
    ),
    path("api/payments/create/", CreatePaymentView.as_view(), name="create-payment"),
    path("api/", include(router.urls)),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/yookassa/webhook/", YooKassaWebhookView.as_view()),

]
