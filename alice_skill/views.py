import logging

from django.db import connection
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
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


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 OK if service is healthy, 503 if database is unreachable.
    """
    try:
        # Check database connectivity
        connection.ensure_connection()
        return Response(
            {'status': 'healthy', 'database': 'connected'}, status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return Response(
            {'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


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
        logger.debug(f'Incoming request: {request.data}')
        request_serializer = AliceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_request = request_serializer.validated_data

        response_text = None
        for handler in self.handlers:
            try:
                response_text = handler.handle(validated_request)
            except Exception as e:
                logger.exception(
                    f'Handler raised an exception:\n {e};\n...continuing to next handler'
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
    """
    API endpoint that allows blood pressure measurements to be viewed or edited.

    Permissions:
    - Authenticated users can access their own measurements.
    - Bot requests with a valid token can access measurements for a specific user_id.
    - Superusers have full access to all measurements.

    Filtering:
    - `user_id`: Filter measurements by Alice User ID (for superusers and bots).
    - `user`: Filter by internal user PK.

    Ordering:
    - `measured_at`: Order by measurement time.
    - `systolic`, `diastolic`, `pulse`: Order by measurement values.
    """

    # Use select_related to avoid N+1 queries when accessing the user relationship
    queryset = BloodPressureMeasurement.objects.select_related('user').order_by(
        '-measured_at'
    )
    serializer_class = BloodPressureMeasurementSerializer
    permission_classes = [IsBot | IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['user']
    search_fields = ['alice_user_id']
    ordering_fields = ['measured_at', 'systolic', 'diastolic', 'pulse']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Dynamically filters the queryset based on the user type and query parameters.
        """
        user = self.request.user
        is_bot_request = getattr(self.request, 'is_bot', False)

        # Case 1: Request is from the bot
        if is_bot_request:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return self.queryset.filter(user__alice_user_id=user_id)
            # If user_id is not provided for a bot request, return no results
            return self.queryset.none()

        # Case 2: User is a superuser
        if user.is_superuser:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return self.queryset.filter(user__alice_user_id=user_id)
            # Superusers can see all measurements if no user_id is specified
            return self.queryset

        # Case 3: Regular authenticated user
        if user.is_authenticated:
            try:
                # Retrieve the AliceUser associated with the Django user
                alice_user = AliceUser.objects.select_related('user').get(user=user)
                return self.queryset.filter(user=alice_user)
            except AliceUser.DoesNotExist:
                # If no AliceUser is linked, return no results
                return self.queryset.none()

        # Case 4: Unauthenticated user (and not a bot)
        # Permissions should handle this, but as a fallback, return no results
        return self.queryset.none()

    def get_serializer_context(self):
        """
        Adds user and timezone information to the serializer context.
        """
        context = super().get_serializer_context()
        user = self.request.user
        is_bot_request = getattr(self.request, 'is_bot', False)

        # For authenticated users, add their AliceUser and timezone to the context
        if user.is_authenticated:
            try:
                alice_user = AliceUser.objects.select_related('user').get(user=user)
                context['alice_user'] = alice_user
                context['timezone'] = alice_user.timezone or 'UTC'
            except AliceUser.DoesNotExist:
                pass  # No linked AliceUser, so no user-specific context is added

        # For bot requests, find the user by user_id and add their info to the context
        elif is_bot_request:
            user_id = self.request.query_params.get('user_id')
            if user_id:
                try:
                    alice_user = AliceUser.objects.get(alice_user_id=user_id)
                    context['alice_user'] = alice_user
                    context['timezone'] = alice_user.timezone or 'UTC'
                    logger.debug(
                        f"Bot request: Found user {user_id} with timezone '{alice_user.timezone}'"
                    )
                except AliceUser.DoesNotExist:
                    logger.warning(
                        f"Bot request: User with alice_user_id '{user_id}' not found"
                    )

        return context


class LinkStatusView(APIView):
    """
    Checks the linking status of a user from either platform.

    Security Note: This endpoint uses AllowAny permission to allow both
    Alice and Telegram bot to check link status. Rate limiting is applied
    to prevent abuse. Consider adding IP-based restrictions or moving to
    IsBot permission for production deployments.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        alice_user_id = request.data.get('session', {}).get('user_id')
        telegram_user_id = request.data.get('telegram_user_id')

        # Validate that at least one identifier is provided
        if not alice_user_id and not telegram_user_id:
            return Response(
                {'status': 'error', 'message': ViewMessages.UNABLE_TO_IDENTIFY_USER},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        if alice_user_id:
            user = AliceUser.objects.filter(alice_user_id=alice_user_id).first()
        elif telegram_user_id:
            user = AliceUser.objects.filter(telegram_user_id=telegram_user_id).first()
        if user:
            if user.telegram_user_id:
                return Response(
                    {'status': 'linked', 'message': LinkStatusViewMessages.LINKED},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        'status': 'not_linked',
                        'message': LinkStatusViewMessages.NOT_LINKED,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {'status': 'error', 'message': ViewMessages.UNABLE_TO_IDENTIFY_USER},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UnlinkView(APIView):
    """
    Handles unlinking a user account from either platform.

    Security Note: This endpoint uses AllowAny permission to allow both
    Alice and Telegram bot to unlink accounts. Rate limiting is applied
    to prevent abuse. Consider adding additional authentication or audit
    logging for production deployments.
    """

    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        try:
            alice_user_id = request.data.get('session', {}).get('user_id')
            telegram_user_id = request.data.get('telegram_user_id')

            # Validate that at least one identifier is provided
            if not alice_user_id and not telegram_user_id:
                return Response(
                    {
                        'status': 'error',
                        'message': ViewMessages.UNABLE_TO_IDENTIFY_USER,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = None
            if alice_user_id:
                user = AliceUser.objects.filter(alice_user_id=alice_user_id).first()
            elif telegram_user_id:
                user = AliceUser.objects.filter(
                    telegram_user_id=telegram_user_id
                ).first()

            if user and user.telegram_user_id:
                user.telegram_user_id = None
                user.save()
                return Response(
                    {'status': 'unlinked', 'message': UnlinkViewMessages.SUCCESS},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {'status': 'not_linked', 'message': UnlinkViewMessages.NOT_LINKED},
                    status=status.HTTP_200_OK,
                )
        except Exception as e:
            logger.exception('Error unlinking account')
            return Response(
                {'status': 'error', 'message': str(e)},
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
                {'status': 'error', 'message': ViewMessages.USER_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )


class GenerateLinkTokenView(APIView):
    """
    Generates a linking token for a Telegram user.
    Note: This view already has application-level rate limiting in generate_link_token().
    DRF throttling provides an additional layer of protection.
    """

    permission_classes = [IsBot]
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
        telegram_user_id = request.data.get('telegram_user_id')
        if not telegram_user_id:
            return Response(
                {
                    'status': 'error',
                    'message': GenerateLinkTokenViewMessages.USER_ID_MISSING,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Ensure telegram_user_id is an integer
            telegram_user_id = int(telegram_user_id)
        except ValueError:
            return Response(
                {
                    'status': 'error',
                    'message': GenerateLinkTokenViewMessages.INVALID_USER_ID,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plaintext_token = generate_link_token(telegram_user_id=telegram_user_id)
            return Response(
                {
                    'status': 'success',
                    'token': plaintext_token,
                    'message': GenerateLinkTokenViewMessages.SUCCESS,
                },
                status=status.HTTP_201_CREATED,
            )
        except TooManyRequests as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception:
            logger.exception('Error generating link token')
            return Response(
                {'status': 'error', 'message': GenerateLinkTokenViewMessages.FAIL},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
