import re
import logging

from ..handlers.base import BaseAliceHandler
from ..serializers import BloodPressureMeasurementSerializer

logger = logging.getLogger(__name__)


class RecordPressureHandler(BaseAliceHandler):
    def handle(self, validated_request_data: dict) -> str | None:
        original_utterance = self.get_original_utterance(validated_request_data).lower()
        logger.debug(
            f"RecordPressureHandler: Processing request: '{original_utterance}'"
        )

        # Normalize: lowercase, replace common separators with a standard form, strip extra spaces
        text = original_utterance.lower().strip()
        text = text.replace(",", " ").replace("/", " на ").replace("-", " ")
        text = re.sub(r"\s+", " ", text)
        logger.debug(f"RecordPressureHandler: Normalized text: '{text}'")

        # Support multiple phrasings: "120 на 80", "давление 120 80", "120/80", "АД 120 на 80"
        # Optionally capture pulse with words like "пульс" or standalone third number
        # Examples: "120 на 80 пульс 70", "АД 120 80 70"
        patterns = [
            r"(?:давление|ад)?\s*(\d{2,3})\s*на\s*(\d{2,3})(?:\s*(?:пульс|пульса|пульс:)\s*(\d{2,3})|\s+(\d{2,3}))?",
            r"(?:давление|ад)?\s*(\d{2,3})\s+(\d{2,3})(?:\s*(?:пульс|пульса|пульс:)\s*(\d{2,3})|\s+(\d{2,3}))?",
        ]

        match = None
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                logger.debug(f"RecordPressureHandler: Pattern matched: {pattern}")
                break

        if not match:
            logger.debug(
                f"RecordPressureHandler: No pattern matched for text: '{text}'"
            )
            return

        systolic = int(match.group(1))
        diastolic = int(match.group(2))
        # Pulse may be in group 3 or 4 depending on which optional matched
        pulse_str = match.group(3) or match.group(4)
        pulse = int(pulse_str) if pulse_str else None

        logger.info(
            f"RecordPressureHandler: Extracted values - systolic: {systolic}, diastolic: {diastolic}, pulse: {pulse}"
        )

        payload = {"systolic": systolic, "diastolic": diastolic}
        if pulse is not None:
            payload["pulse"] = pulse

        serializer = BloodPressureMeasurementSerializer(data=payload)

        if serializer.is_valid():
            instance = serializer.save()
            logger.info(
                f"RecordPressureHandler: Successfully saved measurement: {systolic}/{diastolic}"
                + (f", pulse: {instance.pulse}" if instance.pulse else "")
            )
            if instance.pulse is not None:
                return f"Запомнил давление {systolic} на {diastolic}, пульс {instance.pulse}"
            return f"Запомнил давление {systolic} на {diastolic}"

        logger.debug(
            f"RecordPressureHandler: Invalid measurement data: {serializer.errors}"
        )
        return (
            "Некорректные значения давления. Пожалуйста, проверьте данные и повторите."
        )
