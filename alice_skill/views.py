import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .handlers.record_pressure import RecordPressureHandler
from .serializers import AliceRequestSerializer, AliceResponseSerializer
from .helpers import build_alice_response_payload

logger = logging.getLogger(__name__)

class AliceWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    def post(self, request):
        logger.info(f"Incoming request: {request.data}")
        # 1. Validate incoming request
        request_serializer = AliceRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated_request = request_serializer.validated_data
        
        # 2. Delegate to a handler to get the response content
        handler = RecordPressureHandler()
        response_text = handler.handle(validated_request)
        
        # 3. Build the response payload using the helper
        response_payload = build_alice_response_payload(response_text, validated_request)
        
        # 4. Validate the final response and send it
        response_serializer = AliceResponseSerializer(data=response_payload)
        response_serializer.is_valid(raise_exception=True)
        
        return Response(response_serializer.validated_data)