from django.test import TestCase
from ..models import BloodPressureMeasurement
from ..handlers.record_pressure import RecordPressureHandler


class RecordPressureHandlerTest(TestCase):
    def setUp(self):
        self.handler = RecordPressureHandler()

    def test_handle_success(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        validated_request_data = {
            "request": {"original_utterance": "запомни давление 120 на 80"},
            "session": {},
            "version": "1.0",
        }
        response_text = self.handler.handle(validated_request_data)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 1)
        measurement = BloodPressureMeasurement.objects.first()
        self.assertEqual(measurement.systolic, 120)
        self.assertEqual(measurement.diastolic, 80)
        self.assertEqual(response_text, "Запомнил давление 120 на 80")

    def test_handle_parse_error(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        validated_request_data = {
            "request": {"original_utterance": "какая-то ерунда"},
            "session": {},
            "version": "1.0",
        }
        response_text = self.handler.handle(validated_request_data)
        self.assertEqual(
            response_text,
            "Не удалось распознать цифры давления. Попробуйте сказать, например, ‘давление 120 на 80’.",
        )
