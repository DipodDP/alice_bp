from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AliceWebhookView, BloodPressureMeasurementViewSet

router = DefaultRouter()
router.register(r"measurements", BloodPressureMeasurementViewSet, basename="measurement")

urlpatterns = [
    path("alice_webhook/", AliceWebhookView.as_view(), name="alice-webhook"),
    path("", include(router.urls)),
]
