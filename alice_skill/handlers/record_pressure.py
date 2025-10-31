import re
import logging

from ..messages import RecordPressureMessages


from ..handlers.base import BaseAliceHandler
from ..serializers import BloodPressureMeasurementSerializer
from ..models import AliceUser

logger = logging.getLogger(__name__)


class RecordPressureHandler(BaseAliceHandler):
    def handle(self, validated_request_data: dict) -> str | None:
        tokens = self.get_nlu_tokens(validated_request_data)
        if tokens:
            logger.debug(f"RecordPressureHandler: Processing request tokens: {tokens}")
            # Join tokens into a string and normalize known separators
            text = " ".join(tokens).lower().replace(" x ", " на ")
            logger.debug(
                f"RecordPressureHandler: Normalized text from tokens: '{text}'"
            )
        else:
            original_utterance = self.get_original_utterance(validated_request_data)
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
        pattern = r"(?:давление|ад)?\s*(\d{2,3})\s*(?:на|\s)\s*(\d{2,3})(?:\s*(?:пульс|пульса|пульс:)?\s*(\d{2,3}))?"

        match = re.search(pattern, text)
        if match:
            logger.debug(f"RecordPressureHandler: Pattern matched: {pattern}")

        if not match:
            logger.debug(
                f"RecordPressureHandler: No pattern matched for text: '{text}'"
            )
            return

        systolic = int(match.group(1))
        diastolic = int(match.group(2))
        pulse_str = match.group(3)
        pulse = int(pulse_str) if pulse_str else None

        logger.info(
            f"RecordPressureHandler: Extracted values - systolic: {systolic}, diastolic: {diastolic}, pulse: {pulse}"
        )

        session = validated_request_data.get("session", {})
        user_id = session.get("user_id")
        if not user_id:
            logger.debug("RecordPressureHandler: Missing user_id in session; skipping")
            return

        user_timezone_str = validated_request_data.get("meta", {}).get(
            "timezone", "UTC"
        )
        user, created = AliceUser.objects.get_or_create(alice_user_id=user_id)
        if created:
            logger.info(f"New user created with alice_user_id: {user_id}")
        if user.timezone != user_timezone_str:
            user.timezone = user_timezone_str
            user.save(update_fields=["timezone"])
            logger.info(f"Updated timezone for user {user_id} to {user_timezone_str}")

        payload = {"user": user.pk, "systolic": systolic, "diastolic": diastolic}
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
                return RecordPressureMessages.SUCCESS_WITH_PULSE.format(
                    systolic=systolic, diastolic=diastolic, pulse=instance.pulse
                )
            return RecordPressureMessages.SUCCESS.format(
                systolic=systolic, diastolic=diastolic
            )

        logger.debug(
            f"RecordPressureHandler: Invalid measurement data: {serializer.errors}"
        )
        return RecordPressureMessages.INVALID

        return
