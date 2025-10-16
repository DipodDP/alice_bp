import logging
from .base import BaseAliceHandler
from ..models import BloodPressureMeasurement
from ..serializers import BloodPressureMeasurementSerializer

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
            logger.debug("LastMeasurementHandler: Missing user_id in session; returning no records")
            return "Записей пока нет."
        last = (
            BloodPressureMeasurement.objects.filter(user_id=user_id)
            .order_by("-created_at")
            .first()
        )
        if not last:
            logger.info("LastMeasurementHandler: No measurements found in database")
            return "Записей пока нет."

        serializer = BloodPressureMeasurementSerializer(last)
        data = serializer.data
        reply = f"Последняя запись: {data['systolic']}/{data['diastolic']}"
        if data.get("pulse"):
            reply += f", пульс {data['pulse']}"
        reply += f" (создано {data['created_at']})"

        logger.info(
            f"LastMeasurementHandler: Returning measurement: {data['systolic']}/{data['diastolic']}"
        )
        return reply
