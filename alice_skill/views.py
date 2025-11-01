import logging

from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .messages import (
    GenerateLinkTokenViewMessages,
    UnlinkViewMessages,
    LinkStatusViewMessages,
    ViewMessages,
)
from .helpers import build_alice_response_payload
from .models import BloodPressureMeasurement, AliceUser
from .permissions import IsBot, IsAliceWebhook
from .services import generate_link_token, TooManyRequests
from .serializers import (
    AliceRequestSerializer,
    AliceResponseSerializer,
    BloodPressureMeasurementSerializer,
    AliceUserSerializer,
)
from .handlers.common import StartDialogHandler, UnparsedHandler
from .handlers.link_account import LinkAccountHandler
from .handlers.record_pressure import RecordPressureHandler
from .handlers.last_measurement import LastMeasurementHandler
from .pagination import CustomPageNumberPagination

logger = logging.getLogger(__name__)


class AliceWebhookView(APIView):
    authentication_classes = []
    permission_classes = [IsAliceWebhook]
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
    permission_classes = [IsBot | IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["user"]
    search_fields = ["alice_user_id"]
    ordering_fields = ["measured_at", "systolic", "diastolic", "pulse"]
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        user = self.request.user
        is_bot_request = getattr(
            self.request, "is_bot", False
        )  # Check for the bot flag

        # If the request is from a bot and user_id is provided
        if is_bot_request and "user_id" in self.request.query_params:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                return self.queryset.filter(user__alice_user_id=user_id)
            return (
                self.queryset.none()
            )  # If user_id is not provided, return empty for bot requests

        # If the user is a superuser
        if user.is_superuser:
            user_id = self.request.query_params.get("user_id")
            if user_id:
                return self.queryset.filter(user__alice_user_id=user_id)
            return self.queryset  # Superusers can see all if no user_id specified

        # For regular authenticated users
        if user.is_authenticated:  # Only proceed if authenticated
            try:
                alice_user = AliceUser.objects.get(user=user)
                return self.queryset.filter(user=alice_user)
            except AliceUser.DoesNotExist:
                return self.queryset.none()

        # For unauthenticated users (not bots), return an empty queryset (permissions should handle 403)
        return self.queryset.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:  # Add this check
            try:
                alice_user = AliceUser.objects.get(user=user)
                context["alice_user"] = alice_user
                # Add timezone to context if available
                if alice_user.timezone:
                    context["timezone"] = alice_user.timezone
            except AliceUser.DoesNotExist:
                pass  # Or handle this case as needed, perhaps by not adding alice_user to context
        return context


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
            user = AliceUser.objects.filter(alice_user_id=alice_user_id).first()
        elif telegram_user_id:
            user = AliceUser.objects.filter(telegram_user_id=telegram_user_id).first()
        if user:
            if user.telegram_user_id:
                return Response(
                    {"status": "linked", "message": LinkStatusViewMessages.LINKED},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": "not_linked",
                        "message": LinkStatusViewMessages.NOT_LINKED,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {"status": "error", "message": ViewMessages.UNABLE_TO_IDENTIFY_USER},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UnlinkView(APIView):
    """
    Handles unlinking a user account from either platform.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            alice_user_id = request.data.get("session", {}).get("user_id")
            telegram_user_id = request.data.get("telegram_user_id")

            user = None
            if alice_user_id:
                user = AliceUser.objects.filter(alice_user_id=alice_user_id).first()
            elif telegram_user_id:
                user = AliceUser.objects.filter(
                    telegram_user_id=telegram_user_id
                ).first()
            else:
                return Response(
                    {
                        "status": "error",
                        "message": ViewMessages.UNABLE_TO_IDENTIFY_USER,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user and user.telegram_user_id:
                user.telegram_user_id = None
                user.save()
                return Response(
                    {"status": "unlinked", "message": UnlinkViewMessages.SUCCESS},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": "not_linked", "message": UnlinkViewMessages.NOT_LINKED},
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            logger.exception("Error unlinking account")
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserByTelegramView(APIView):
    """
    Retrieves a user by their Telegram ID.
    """

    permission_classes = [IsBot]

    def get(self, request, telegram_id, *args, **kwargs):
        try:
            user = AliceUser.objects.get(telegram_user_id=telegram_id)
            serializer = AliceUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AliceUser.DoesNotExist:
            return Response(
                {"status": "error", "message": ViewMessages.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )


class GenerateLinkTokenView(APIView):
    """
    Generates a linking token for a Telegram user.
    """

    permission_classes = [IsBot]  # TODO: Add proper authentication for Telegram bot

    def post(self, request, *args, **kwargs):
        telegram_user_id = request.data.get("telegram_user_id")
        if not telegram_user_id:
            return Response(
                {
                    "status": "error",
                    "message": GenerateLinkTokenViewMessages.USER_ID_MISSING,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Ensure telegram_user_id is an integer
            telegram_user_id = int(telegram_user_id)
        except ValueError:
            return Response(
                {
                    "status": "error",
                    "message": GenerateLinkTokenViewMessages.INVALID_USER_ID,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plaintext_token = generate_link_token(telegram_user_id=telegram_user_id)
            return Response(
                {
                    "status": "success",
                    "token": plaintext_token,
                    "message": GenerateLinkTokenViewMessages.SUCCESS,
                },
                status=status.HTTP_201_CREATED,
            )
        except TooManyRequests as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception:
            logger.exception("Error generating link token")
            return Response(
                {"status": "error", "message": GenerateLinkTokenViewMessages.FAIL},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
