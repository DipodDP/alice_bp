# project urls.py или tgbot_bg/urls.py
from django.urls import path
from django.conf import settings
from . import views

webhook_path = getattr(settings, "WEBHOOK_PATH", "/webhook")

urlpatterns = [
    path("background/", views.home, name="app_home"),
    path("background/start/", views.start, name="app_start"),
    path(f"{webhook_path.lstrip('/')}", views.webhook_handler, name="app_webhook"),
]
