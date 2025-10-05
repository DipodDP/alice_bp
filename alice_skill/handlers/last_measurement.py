from .base import BaseHandler
from ..models import BloodPressureMeasurement
from ..serializers import BloodPressureMeasurementSerializer


class LastMeasurementHandler(BaseHandler):
    """Возвращает последнее измерение, если пользователь просит показать/последнее/давление."""

    KEYWORDS = ["последн", "покажи", "давлен"]

    def handle(self, validated_request_data: dict) -> str | None:
        user_request = self.get_original_utterance(validated_request_data).lower()
        if not any(k in user_request for k in self.KEYWORDS):
            return

        last = BloodPressureMeasurement.objects.order_by("-created_at").first()
        if not last:
            return "Записей пока нет."

        serializer = BloodPressureMeasurementSerializer(last)
        data = serializer.data
        reply = f"Последняя запись: {data['systolic']}/{data['diastolic']}"
        if data.get("pulse"):
            reply += f", пульс {data['pulse']}"
        reply += f" (создано {data['created_at']})"
        return reply
