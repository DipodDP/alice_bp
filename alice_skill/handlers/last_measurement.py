import logging

from ..messages import LastMeasurementMessages
from .base import BaseAliceHandler
from ..models import BloodPressureMeasurement, AliceUser
from ..serializers import BloodPressureMeasurementSerializer
from ..helpers import format_measured_at
from django.utils import timezone


logger = logging.getLogger(__name__)


class LastMeasurementHandler(BaseAliceHandler):
    """Возвращает последнее измерение, если пользователь просит показать/последнее/давление."""

    KEYWORDS = ["последн", "покажи", "давлен"]

    def handle(self, validated_request_data: dict) -> str | None:
        original_utterance = self.get_original_utterance(validated_request_data).lower()
        logger.debug(
            f"LastMeasurementHandler: Processing request: '{original_utterance}'"
        )

        if not any(k in original_utterance for k in self.KEYWORDS):
            logger.debug(
                f"LastMeasurementHandler: No keywords matched in request: '{original_utterance}'"
            )
            return

        logger.debug("LastMeasurementHandler: Fetching last blood pressure measurement")
        session = validated_request_data.get("session", {})
        user_id = session.get("user_id")
        if not user_id:
            return LastMeasurementMessages.NO_RECORDS

        try:
            user = AliceUser.objects.get(alice_user_id=user_id)
        except AliceUser.DoesNotExist:
            return LastMeasurementMessages.NO_RECORDS

        last = (
            BloodPressureMeasurement.objects.filter(user=user)
            .order_by("-measured_at")
            .first()
        )
        if not last:
            logger.info("LastMeasurementHandler: No measurements found in database")
            return LastMeasurementMessages.NO_RECORDS

        serializer = BloodPressureMeasurementSerializer(last)
        data = serializer.data
        reply = LastMeasurementMessages.REPLY.format(
            systolic=data["systolic"], diastolic=data["diastolic"]
        )
        if data.get("pulse"):
            reply += LastMeasurementMessages.PULSE.format(pulse=data["pulse"])
        user_timezone_str = validated_request_data.get("meta", {}).get(
            "timezone", "UTC"
        )
        reply += f"({format_measured_at(data['measured_at'], user_timezone_str, timezone.now())})"

        logger.info(
            f"LastMeasurementHandler: Returning measurement: {data['systolic']}/{data['diastolic']}"
        )
        return reply
