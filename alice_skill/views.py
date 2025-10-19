import logging
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status

from .models import BloodPressureMeasurement, User, LinkToken
from .serializers import BloodPressureMeasurementSerializer
from .handlers.record_pressure import RecordPressureHandler
from .handlers.last_measurement import LastMeasurementHandler
from .handlers.link_account import LinkAccountHandler
from .handlers.common import StartDialogHandler, UnparsedHandler
from .serializers import AliceRequestSerializer, AliceResponseSerializer
from .helpers import build_alice_response_payload
from .services import initiate_linking_process

logger = logging.getLogger(__name__)


# Placeholder authenticators
def validate_alice_signature(request_body, headers):
    """Placeholder for Yandex.Dialogs signature validation."""
    return True


def validate_telegram_bot_request(headers):
    """Placeholder for Telegram bot request validation."""
    # In a real app, you'd check a secret token like:
    # return headers.get("X-Bot-Token") == settings.TELEGRAM_BOT_SECRET_TOKEN
    return True


class AliceWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    handlers = [
        StartDialogHandler(),
        LinkAccountHandler(),
        RecordPressureHandler(),
        LastMeasurementHandler(),
        UnparsedHandler(),
    ]

    def post(self, request):
        logger.info(f"Incoming request: {request.data}")
        # 1. Validate incoming request
        request_serializer = AliceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_request = request_serializer.validated_data

        # 2. Try multiple handlers in order to get the response content;
        # stop at the first that returns a response
        response_text = None
        for handler in self.handlers:
            try:
                response_text = handler.handle(validated_request)
            except Exception as e:
                logger.exception(
                    f"Handler raised an exception:\n {e};\n...continuing to next handler"
                )
                continue
            if response_text:
                break

        # 3. Build the response payload using the helper
        response_payload = build_alice_response_payload(
            response_text, validated_request
        )

        # 4. Validate the final response and send it
        response_serializer = AliceResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.validated_data)


class BloodPressureMeasurementViewSet(viewsets.ModelViewSet):
    queryset = BloodPressureMeasurement.objects.all().order_by("-created_at")
    serializer_class = BloodPressureMeasurementSerializer


class InitiateLinkView(APIView):
    """
    Handles the first step of the linking process, initiated by Alice.
    Generates and returns a one-time code.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        alice_user_id = request.data.get("session", {}).get("user_id")
        if not alice_user_id:
            return Response({"status": "error", "message": "user_id is missing"}, status=status.HTTP_400_BAD_REQUEST)

        success, message = initiate_linking_process(alice_user_id)

        if success:
            return Response({"status": "success", "message": message}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": "error", "message": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LinkStatusView(APIView):
    """
    Checks the linking status of a user from either platform.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        alice_user_id = request.data.get("session", {}).get("user_id")
        telegram_user_id = request.data.get("telegram_user_id")

        user = None
        if alice_user_id:
            user = User.objects.filter(alice_user_id=alice_user_id).first()
        elif telegram_user_id:
            user = User.objects.filter(telegram_user_id=telegram_user_id).first()
        else:
            return Response({"status": "error", "message": "Не удалось определить пользователя."}, status=status.HTTP_400_BAD_REQUEST)

        if user and user.alice_user_id and user.telegram_user_id:
            return Response({"status": "linked", "message": "Аккаунты успешно связаны."}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "not_linked", "message": "Аккаунты не связаны."}, status=status.HTTP_200_OK)


class UnlinkView(APIView):
    """
    Handles unlinking a user account from either platform.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        alice_user_id = request.data.get("session", {}).get("user_id")
        telegram_user_id = request.data.get("telegram_user_id")

        user = None
        if alice_user_id:
            user = User.objects.filter(alice_user_id=alice_user_id).first()
        elif telegram_user_id:
            user = User.objects.filter(telegram_user_id=telegram_user_id).first()
        else:
            return Response({"status": "error", "message": "Не удалось определить пользователя."}, status=status.HTTP_400_BAD_REQUEST)

        if user and user.telegram_user_id:
            user.telegram_user_id = None
            user.save()
            return Response({"status": "unlinked", "message": "Аккаунты успешно отвязаны."}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "not_linked", "message": "Аккаунты не были связаны."}, status=status.HTTP_200_OK)


class CompleteLinkView(APIView):
    """
    Handles the second step, completing the link from Telegram.
    Validates the one-time code and links the accounts.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # if not validate_telegram_bot_request(request.headers):
        #     return Response({"status": "error", "message": "Invalid origin"}, status=status.HTTP_403_FORBIDDEN)

        telegram_user_id = request.data.get("telegram_user_id")
        token = request.data.get("token")

        if not telegram_user_id or not token:
            return Response({"status": "error", "message": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        raw_token = token.replace("-", "").upper()
        token_hash = hmac.new(
            settings.SECRET_KEY.encode(),
            raw_token.encode(),
            'sha256'
        ).hexdigest()

        try:
            link_token = LinkToken.objects.select_related('user').get(token_hash=token_hash)
        except LinkToken.DoesNotExist:
            return Response({"status": "error", "message": "Неверный код или срок его действия истек."}, status=status.HTTP_404_NOT_FOUND)

        if link_token.expires_at < timezone.now():
            link_token.delete()
            return Response({"status": "error", "message": "Неверный код или срок его действия истек."}, status=status.HTTP_410_GONE)

        user = link_token.user

        # Break any existing link for this telegram_user_id
        User.objects.filter(telegram_user_id=telegram_user_id).exclude(id=user.id).update(telegram_user_id=None)

        user.telegram_user_id = telegram_user_id
        user.save()

        link_token.delete()

        return Response({"status": "success", "message": "Аккаунты успешно связаны!"}, status=status.HTTP_200_OK)