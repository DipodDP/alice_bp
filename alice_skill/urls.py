from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AliceWebhookView,
    BloodPressureMeasurementViewSet,
    InitiateLinkView,
    LinkStatusView,
    UnlinkView,
    CompleteLinkView,
)

router = DefaultRouter()
router.register(r"measurements", BloodPressureMeasurementViewSet, basename="measurement")

urlpatterns = [
    path("alice_webhook/", AliceWebhookView.as_view(), name="alice-webhook"),
    path("api/v1/link/initiate/", InitiateLinkView.as_view(), name="link-initiate"),
    path("api/v1/link/status/", LinkStatusView.as_view(), name="link-status"),
    path("api/v1/link/unlink/", UnlinkView.as_view(), name="link-unlink"),
    path("api/v1/link/complete/", CompleteLinkView.as_view(), name="link-complete"),
    path("", include(router.urls)),
]