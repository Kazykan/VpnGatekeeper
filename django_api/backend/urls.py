from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import include, path

from myapp.views import (
    AllAmneziaStatsView,
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
    path("api/", include(router.urls)),
]
