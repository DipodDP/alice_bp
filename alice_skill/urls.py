from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AliceWebhookView,
    BloodPressureMeasurementViewSet,
    LinkStatusView,
    UnlinkView,
    UserByTelegramView,
    GenerateLinkTokenView,
)

router = DefaultRouter()
router.register(r"measurements", BloodPressureMeasurementViewSet, basename="measurement")

urlpatterns = [
    path("alice_webhook/", AliceWebhookView.as_view(), name="alice-webhook"),
    path("api/v1/link/status/", LinkStatusView.as_view(), name="link-status"),
    path("api/v1/link/unlink/", UnlinkView.as_view(), name="link-unlink"),
    path("api/v1/users/by-telegram/<str:telegram_id>/", UserByTelegramView.as_view(), name="user-by-telegram"),
    path("api/v1/link/generate-token/", GenerateLinkTokenView.as_view(), name="link-generate-token"),
    path("", include(router.urls)),
]