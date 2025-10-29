from rest_framework.permissions import BasePermission
from django.conf import settings


class IsBot(BasePermission):
    """
    Allows access only to requests with a valid bot token.
    """

    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False

        try:
            _, token = auth_header.split()
            return token == settings.API_TOKEN
        except (ValueError, AttributeError):
            return False


class IsAliceWebhook(BasePermission):
    """
    Allows access only to requests with a valid Alice webhook secret token
    provided as a query parameter.
    """

    def has_permission(self, request, view):
        token = request.query_params.get("token")
        expected_secret = getattr(settings, "ALICE_WEBHOOK_SECRET", None)

        if not expected_secret or not token or token != expected_secret:
            return False

        return True
