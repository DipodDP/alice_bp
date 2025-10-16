from rest_framework import serializers
from .models import BloodPressureMeasurement


class BloodPressureMeasurementSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(required=True, allow_blank=False)
    MIN_SYSTOLIC = 50
    MAX_SYSTOLIC = 300
    MIN_DIASTOLIC = 30
    MAX_DIASTOLIC = 200
    MIN_PULSE = 20
    MAX_PULSE = 300

    def validate_systolic(self, value):
        if not (self.MIN_SYSTOLIC <= value <= self.MAX_SYSTOLIC):
            raise serializers.ValidationError(
                f"Systolic must be between {self.MIN_SYSTOLIC} and {self.MAX_SYSTOLIC}."
            )
        return value

    def validate_diastolic(self, value):
        if not (self.MIN_DIASTOLIC <= value <= self.MAX_DIASTOLIC):
            raise serializers.ValidationError(
                f"Diastolic must be between {self.MIN_DIASTOLIC} and {self.MAX_DIASTOLIC}."
            )
        return value

    def validate(self, attrs):
        systolic = attrs.get("systolic")
        diastolic = attrs.get("diastolic")
        pulse = attrs.get("pulse")
        if systolic is not None and diastolic is not None and systolic <= diastolic:
            raise serializers.ValidationError(
                "Systolic must be greater than diastolic."
            )
        if pulse is not None and not (self.MIN_PULSE <= pulse <= self.MAX_PULSE):
            raise serializers.ValidationError(
                f"Pulse must be between {self.MIN_PULSE} and {self.MAX_PULSE}."
            )
        return attrs

    class Meta:
        model = BloodPressureMeasurement
        fields = ["user_id", "systolic", "diastolic", "pulse", "created_at"]


# --- Request Serializers ---
class RequestObjectSerializer(serializers.Serializer):
    original_utterance = serializers.CharField(
        allow_blank=True, required=False, default=""
    )
    command = serializers.CharField(allow_blank=True, required=False, default="")


class SessionObjectSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    user_id = serializers.CharField()
    new = serializers.BooleanField(required=False, default=False)


class AliceRequestSerializer(serializers.Serializer):
    request = RequestObjectSerializer()
    session = SessionObjectSerializer()
    version = serializers.CharField()


# --- Response Serializers ---
class ResponseObjectSerializer(serializers.Serializer):
    text = serializers.CharField()
    end_session = serializers.BooleanField(default=False)


class AliceResponseSerializer(serializers.Serializer):
    response = ResponseObjectSerializer()
    session = SessionObjectSerializer()
    version = serializers.CharField()
