import logging

from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import build_alice_response_payload
from .models import BloodPressureMeasurement, User
from .permissions import IsBot
from .services import generate_link_token, TooManyRequests
from .serializers import (
    AliceRequestSerializer,
    AliceResponseSerializer,
    BloodPressureMeasurementSerializer,
    UserSerializer,
)
from .handlers.common import StartDialogHandler, UnparsedHandler
from .handlers.link_account import LinkAccountHandler
from .handlers.record_pressure import RecordPressureHandler
from .handlers.last_measurement import LastMeasurementHandler

logger = logging.getLogger(__name__)


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
        logger.debug(f"Incoming request: {request.data}")
        request_serializer = AliceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_request = request_serializer.validated_data

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

        response_payload = build_alice_response_payload(
            response_text, validated_request
        )

        response_serializer = AliceResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.validated_data)


class BloodPressureMeasurementViewSet(viewsets.ModelViewSet):
    queryset = BloodPressureMeasurement.objects.all().order_by("-measured_at")
    serializer_class = BloodPressureMeasurementSerializer


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


class UserByTelegramView(APIView):
    """
    Retrieves a user by their Telegram ID.
    """
    permission_classes = [IsBot]  # In production, should be protected

    def get(self, request, telegram_id, *args, **kwargs):
        try:
            user = User.objects.get(telegram_user_id=telegram_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class GenerateLinkTokenView(APIView):
    """
    Generates a linking token for a Telegram user.
    """
    permission_classes = [IsBot] # TODO: Add proper authentication for Telegram bot

    def post(self, request, *args, **kwargs):
        telegram_user_id = request.data.get("telegram_user_id")
        if not telegram_user_id:
            return Response({"status": "error", "message": "telegram_user_id is missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure telegram_user_id is an integer
            telegram_user_id = int(telegram_user_id)
        except ValueError:
            return Response({"status": "error", "message": "Invalid telegram_user_id format"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plaintext_token = generate_link_token(telegram_user_id=telegram_user_id)
            return Response({"status": "success", "token": plaintext_token, "message": "Token generated successfully"}, status=status.HTTP_201_CREATED)
        except TooManyRequests as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as e:
            logger.exception("Error generating link token")
            return Response({"status": "error", "message": "Failed to generate token"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)