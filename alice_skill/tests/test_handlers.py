from django.test import TestCase
from ..models import BloodPressureMeasurement
from ..handlers.record_pressure import RecordPressureHandler
from ..handlers.last_measurement import LastMeasurementHandler


class RecordPressureHandlerTest(TestCase):
    def setUp(self):
        self.handler = RecordPressureHandler()

    def test_handle_success(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        validated_request_data = {
            "request": {"original_utterance": "запомни давление 120 на 80"},
            "session": {"user_id": "u"},
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
            None,
        )


class LastMeasurementHandlerTest(TestCase):
    def setUp(self):
        self.handler = LastMeasurementHandler()

    def test_handle_with_measurements(self):
        """Test handler returns last measurement when measurements exist."""
        # Create test measurements
        BloodPressureMeasurement.objects.create(user_id="u", systolic=120, diastolic=80, pulse=70)
        BloodPressureMeasurement.objects.create(user_id="u", systolic=130, diastolic=85, pulse=75)

        validated_request_data = {
            "request": {"original_utterance": "покажи последнее давление"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        # Should return the most recent measurement (measurement2)
        self.assertIn("130/85", response_text)
        self.assertIn("пульс 75", response_text)
        self.assertIn("Последняя запись:", response_text)

    def test_handle_without_pulse(self):
        """Test handler works when measurement has no pulse."""
        BloodPressureMeasurement.objects.create(user_id="u", systolic=110, diastolic=70, pulse=None)

        validated_request_data = {
            "request": {"original_utterance": "последнее давление"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        self.assertIn("110/70", response_text)
        self.assertNotIn("пульс", response_text)
        self.assertIn("Последняя запись:", response_text)

    def test_handle_no_measurements(self):
        """Test handler returns appropriate message when no measurements exist."""
        validated_request_data = {
            "request": {"original_utterance": "покажи давление"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        self.assertEqual(response_text, "Записей пока нет.")

    def test_handle_no_keywords(self):
        """Test handler returns None when no keywords match."""
        BloodPressureMeasurement.objects.create(user_id="u", systolic=120, diastolic=80)

        validated_request_data = {
            "request": {"original_utterance": "какая-то ерунда"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        self.assertIsNone(response_text)

    def test_handle_partial_keyword_match(self):
        """Test handler works with partial keyword matches."""
        BloodPressureMeasurement.objects.create(user_id="u", systolic=125, diastolic=82)

        validated_request_data = {
            "request": {"original_utterance": "последнее"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        self.assertIn("125/82", response_text)
        self.assertIn("Последняя запись:", response_text)

    def test_handle_case_insensitive(self):
        """Test handler works with different cases."""
        BloodPressureMeasurement.objects.create(user_id="u", systolic=115, diastolic=75)

        validated_request_data = {
            "request": {"original_utterance": "ПОКАЖИ ДАВЛЕНИЕ"},
            "session": {"user_id": "u"},
            "version": "1.0",
        }

        response_text = self.handler.handle(validated_request_data)

        self.assertIn("115/75", response_text)
        self.assertIn("Последняя запись:", response_text)
