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
