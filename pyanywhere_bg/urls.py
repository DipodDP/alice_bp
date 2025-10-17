# project urls.py или tgbot_bg/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("background/", views.home, name="app_home"),
    path("background/start/", views.start, name="app_start"),
    path(f"{views.WEBHOOK_PATH.lstrip('/')}", views.webhook_handler, name="app_webhook"),
]
