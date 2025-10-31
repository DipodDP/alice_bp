from datetime import datetime, timezone
from ..models import BloodPressureMeasurement

class TestDataFactory:
    @staticmethod
    def create_measurement(user, systolic, diastolic, pulse=None, measured_at=None):
        if measured_at is None:
            measured_at = datetime.now(timezone.utc)
        return BloodPressureMeasurement.objects.create(
            user=user,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            measured_at=measured_at,
        )

    @staticmethod
    def create_validated_request_data(original_utterance, user_id='u', timezone='UTC'):
        return {
            "meta": {"timezone": timezone},
            "request": {"original_utterance": original_utterance},
            "session": {"user_id": user_id},
            "version": "1.0",
        }
