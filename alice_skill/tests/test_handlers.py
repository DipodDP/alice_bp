from django.test import TestCase
from datetime import timedelta, datetime
from datetime import timezone as dt_timezone
from unittest import mock

from ..messages import (
    DateFormattingMessages,
    LastMeasurementMessages,
    RecordPressureMessages,
)

from ..models import BloodPressureMeasurement, AliceUser
from ..handlers.record_pressure import RecordPressureHandler
from ..handlers.last_measurement import LastMeasurementHandler
from .factories import TestDataFactory


class RecordPressureHandlerTest(TestCase):
    def setUp(self):
        self.handler = RecordPressureHandler()
        self.factory = TestDataFactory()

    def test_handle_success(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="запомни давление 120 на 80"
        )
        response_text = self.handler.handle(validated_request_data)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 1)
        measurement = BloodPressureMeasurement.objects.first()
        self.assertEqual(measurement.systolic, 120)
        self.assertEqual(measurement.diastolic, 80)
        self.assertEqual(
            response_text,
            RecordPressureMessages.SUCCESS.format(systolic=120, diastolic=80),
        )

    def test_handle_parse_error(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="какая-то ерунда", user_id=None
        )
        response_text = self.handler.handle(validated_request_data)
        self.assertEqual(
            response_text,
            None,
        )


class LastMeasurementHandlerTest(TestCase):
    def setUp(self):
        self.handler = LastMeasurementHandler()
        self.factory = TestDataFactory()
        self.user = AliceUser.objects.create(alice_user_id='u')

    @mock.patch("django.utils.timezone.now")
    def test_handle_with_measurements(self, mock_now):
        """Test handler returns last measurement when measurements exist."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        # Create test measurements
        self.factory.create_measurement(
            user=self.user,
            systolic=120,
            diastolic=80,
            pulse=70,
            measured_at=mock_now.return_value - timedelta(minutes=10),
        )
        self.factory.create_measurement(
            user=self.user,
            systolic=130,
            diastolic=85,
            pulse=75,
            measured_at=mock_now.return_value,
        )

        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="покажи последнее давление"
        )

        response_text = self.handler.handle(validated_request_data)

        # Should return the most recent measurement (measurement2)
        expected_text = LastMeasurementMessages.REPLY.format(systolic=130, diastolic=85)
        expected_text += LastMeasurementMessages.PULSE.format(pulse=75)
        expected_text += f"({DateFormattingMessages.TODAY} {DateFormattingMessages.PREPOSITION} 12:00)"
        self.assertEqual(response_text, expected_text)

    @mock.patch("django.utils.timezone.now")
    def test_handle_without_pulse(self, mock_now):
        """Test handler works when measurement has no pulse."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        self.factory.create_measurement(
            user=self.user,
            systolic=110,
            diastolic=70,
            pulse=None,
            measured_at=mock_now.return_value,
        )

        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="последнее давление"
        )

        response_text = self.handler.handle(validated_request_data)

        expected_text = LastMeasurementMessages.REPLY.format(systolic=110, diastolic=70)
        expected_text += f"({DateFormattingMessages.TODAY} {DateFormattingMessages.PREPOSITION} 12:00)"
        self.assertEqual(response_text, expected_text)

    @mock.patch("django.utils.timezone.now")
    def test_handle_no_measurements(self, mock_now):
        """Test handler returns appropriate message when no measurements exist."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="покажи давление"
        )

        response_text = self.handler.handle(validated_request_data)

        self.assertEqual(response_text, LastMeasurementMessages.NO_RECORDS)

    @mock.patch("django.utils.timezone.now")
    def test_handle_no_keywords(self, mock_now):
        """Test handler returns None when no keywords match."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        self.factory.create_measurement(
            user=self.user, systolic=120, diastolic=80, measured_at=mock_now.return_value
        )

        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="какая-то ерунда"
        )

        response_text = self.handler.handle(validated_request_data)

        self.assertIsNone(response_text)

    @mock.patch("django.utils.timezone.now")
    def test_handle_partial_keyword_match(self, mock_now):
        """Test handler works with partial keyword matches."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        self.factory.create_measurement(
            user=self.user, systolic=125, diastolic=82, measured_at=mock_now.return_value
        )

        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="последнее"
        )

        response_text = self.handler.handle(validated_request_data)

        expected_text = LastMeasurementMessages.REPLY.format(systolic=125, diastolic=82)
        expected_text += f"({DateFormattingMessages.TODAY} {DateFormattingMessages.PREPOSITION} 12:00)"
        self.assertEqual(response_text, expected_text)

    @mock.patch("django.utils.timezone.now")
    def test_handle_case_insensitive(self, mock_now):
        """Test handler works with different cases."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now
        self.factory.create_measurement(
            user=self.user, systolic=115, diastolic=75, measured_at=mock_now.return_value
        )

        validated_request_data = self.factory.create_validated_request_data(
            original_utterance="ПОКАЖИ ДАВЛЕНИЕ"
        )

        response_text = self.handler.handle(validated_request_data)

        expected_text = LastMeasurementMessages.REPLY.format(systolic=115, diastolic=75)
        expected_text += f"({DateFormattingMessages.TODAY} {DateFormattingMessages.PREPOSITION} 12:00)"
        self.assertEqual(response_text, expected_text)

    @mock.patch("django.utils.timezone.now")
    def test_handle_date_formats(self, mock_now):
        """Test handler returns correct date formats for different measurement dates."""
        fixed_now = datetime(2025, 10, 24, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_now.return_value = fixed_now

        test_cases = [
            (
                timedelta(days=1),
                f"{DateFormattingMessages.YESTERDAY} {DateFormattingMessages.PREPOSITION} 12:00",
            ),
            (
                timedelta(days=2),
                f"{DateFormattingMessages.DAY_BEFORE_YESTERDAY} {DateFormattingMessages.PREPOSITION} 12:00",
            ),
            (
                timedelta(days=3),
                (mock_now.return_value - timedelta(days=3))
                .astimezone(dt_timezone.utc)
                .strftime("%d.%m.%Y"),
            ),
        ]

        for delta, expected_date_str in test_cases:
            with self.subTest(delta=delta):
                BloodPressureMeasurement.objects.all().delete()
                measurement_time = mock_now.return_value - delta
                self.factory.create_measurement(
                    user=self.user,
                    systolic=120,
                    diastolic=80,
                    measured_at=measurement_time,
                )
                validated_request_data = self.factory.create_validated_request_data(
                    original_utterance="покажи последнее давление"
                )
                response_text = self.handler.handle(validated_request_data)
                self.assertIn(expected_date_str, response_text)
