import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework.filters import OrderingFilter

from .filters import BloodPressureMeasurementFilter
from .messages import (
    GenerateLinkTokenViewMessages,
    UnlinkViewMessages,
    LinkStatusViewMessages,
    ViewMessages,
)
from .helpers import build_alice_response_payload, get_user_context, get_hashed_telegram_id
from .models import BloodPressureMeasurement, AliceUser
from .permissions import IsBot, IsAliceWebhook
from .services import (
    generate_link_token,
    TooManyRequests,
    get_alice_user,
    process_alice_request,
    check_health,
)
from .serializers import (
    AliceRequestSerializer,
    AliceResponseSerializer,
    BloodPressureMeasurementSerializer,
    AliceUserSerializer,
    GenerateLinkTokenRequestSerializer,
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
    health = check_health()
    if health['status'] == 'healthy':
        return Response(health, status=status.HTTP_200_OK)
    return Response(health, status=status.HTTP_503_SERVICE_UNAVAILABLE)


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

        response_text = process_alice_request(self.handlers, validated_request)

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
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_class = BloodPressureMeasurementFilter
    search_fields = ['alice_user_id']
    ordering_fields = ['measured_at', 'systolic', 'diastolic', 'pulse']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        """
        Dynamically filters the queryset based on the user.
        Date range filtering is handled by DjangoFilterBackend.
        """
        queryset = super().get_queryset()
        return queryset.for_user(self.request)

    def get_serializer_context(self):
        """
        Adds user and timezone information to the serializer context.
        """
        context = super().get_serializer_context()
        context.update(get_user_context(self.request))
        return context


class UserAwareAPIView(APIView):
    def get_user_from_request(self, request):
        alice_user_id = request.data.get('session', {}).get('user_id')
        telegram_user_id = request.data.get('telegram_user_id')
        return get_alice_user(
            alice_user_id=alice_user_id, telegram_user_id=telegram_user_id
        )


class LinkStatusView(UserAwareAPIView):
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
        user = self.get_user_from_request(request)

        if not user:
            return Response(
                {'status': 'error', 'message': ViewMessages.UNABLE_TO_IDENTIFY_USER},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.telegram_user_id_hash:
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


class UnlinkView(UserAwareAPIView):
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
            user = self.get_user_from_request(request)

            if not user:
                return Response(
                    {
                        'status': 'error',
                        'message': ViewMessages.UNABLE_TO_IDENTIFY_USER,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.telegram_user_id_hash:
                user.telegram_user_id_hash = None
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
            hashed_telegram_id = get_hashed_telegram_id(telegram_id)
            user = AliceUser.objects.get(telegram_user_id_hash=hashed_telegram_id)
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
        serializer = GenerateLinkTokenRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'status': 'error', 'message': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        telegram_user_id = serializer.validated_data['telegram_user_id']

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
