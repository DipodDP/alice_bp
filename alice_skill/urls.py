from django.urls import path
from .views import AliceWebhookView

urlpatterns = [
    path("", AliceWebhookView.as_view(), name="alice-webhook"),
]
