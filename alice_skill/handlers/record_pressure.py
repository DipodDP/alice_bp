import re
from ..serializers import BloodPressureMeasurementSerializer


class RecordPressureHandler:
    def handle(self, validated_data):
        req = validated_data["request"]
        session = validated_data.get("session", {})
        original_utterance = req.get("original_utterance", "") or req.get("command", "")

        if not original_utterance and session.get("new"):
            return "Здравствуйте! Скажите давление, например: 120 на 80."

        # Normalize: lowercase, replace common separators with a standard form, strip extra spaces
        text = original_utterance.lower().strip()
        text = text.replace(",", " ").replace("/", " на ").replace("-", " ")
        text = re.sub(r"\s+", " ", text)

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
                break

        if not match:
            return

        systolic = int(match.group(1))
        diastolic = int(match.group(2))
        # Pulse may be in group 3 or 4 depending on which optional matched
        pulse_str = match.group(3) or match.group(4)
        pulse = int(pulse_str) if pulse_str else None

        payload = {"systolic": systolic, "diastolic": diastolic}
        if pulse is not None:
            payload["pulse"] = pulse

        serializer = BloodPressureMeasurementSerializer(data=payload)

        if serializer.is_valid():
            instance = serializer.save()
            if instance.pulse is not None:
                return f"Запомнил давление {systolic} на {diastolic}, пульс {instance.pulse}"
            return f"Запомнил давление {systolic} на {diastolic}"
        return (
            "Некорректные значения давления. Пожалуйста, проверьте данные и повторите."
        )
