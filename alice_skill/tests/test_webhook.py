from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from ..messages import (
    HandlerMessages,
    LastMeasurementMessages,
    RecordPressureMessages,
)
from ..models import BloodPressureMeasurement, AliceUser


@override_settings(ALICE_WEBHOOK_SECRET="test-secret")
class AliceWebhookViewTest(APITestCase):
    def setUp(self):
        self.url = reverse("alice-webhook")
        self.token = "test-secret"

    def test_webhook_success(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        payload = {
            "meta": {"timezone": "UTC"},
            "request": {
                "original_utterance": "запомни давление 130 на 75",
                "type": "SimpleUtterance",
            },
            "session": {"session_id": "123-456", "user_id": "test-user"},
            "version": "1.0",
        }
        response = self.client.post(f"{self.url}?token={self.token}", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BloodPressureMeasurement.objects.count(), 1)
        measurement = BloodPressureMeasurement.objects.first()
        user = AliceUser.objects.get(alice_user_id="test-user")
        self.assertEqual(measurement.user, user)
        self.assertEqual(measurement.systolic, 130)
        self.assertEqual(measurement.diastolic, 75)
        expected_response = {
            "response": {
                "text": RecordPressureMessages.SUCCESS.format(
                    systolic=130, diastolic=75
                ),
                "end_session": False,
            },
            "session": {**payload["session"], "new": False},
            "version": "1.0",
        }
        self.assertDictEqual(response.data, expected_response)

    def test_webhook_bad_request(self):
        payload = {
            "session": {"session_id": "123-456", "user_id": "test-user"},
            "version": "1.0",
        }
        response = self.client.post(f"{self.url}?token={self.token}", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_webhook_empty_utterance_new_session(self):
        payload = {
            "meta": {"timezone": "UTC"},
            "request": {"original_utterance": "", "command": ""},
            "session": {"session_id": "s", "user_id": "u", "new": True},
            "version": "1.0",
        }
        response = self.client.post(f"{self.url}?token={self.token}", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(HandlerMessages.GREETING, response.data["response"]["text"])

    def test_last_measurement_no_records(self):
        self.assertEqual(BloodPressureMeasurement.objects.count(), 0)
        payload = {
            "meta": {"timezone": "UTC"},
            "request": {"original_utterance": "покажи последнее давление"},
            "session": {"session_id": "last-1", "user_id": "u1"},
            "version": "1.0",
        }
        response = self.client.post(f"{self.url}?token={self.token}", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["response"]["text"], LastMeasurementMessages.NO_RECORDS
        )
        self.assertEqual(
            response.data["session"]["session_id"], payload["session"]["session_id"]
        )
        self.assertEqual(response.data["version"], payload["version"])

    def test_last_measurement_with_record(self):
        user = AliceUser.objects.create(alice_user_id="u2")
        BloodPressureMeasurement.objects.create(
            user=user, systolic=120, diastolic=80, pulse=70
        )
        payload = {
            "meta": {"timezone": "UTC"},
            "request": {"original_utterance": "покажи последнее давление"},
            "session": {"session_id": "last-2", "user_id": "u2"},
            "version": "1.0",
        }
        response = self.client.post(f"{self.url}?token={self.token}", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        text = response.data["response"]["text"]
        self.assertIn(
            LastMeasurementMessages.REPLY.format(systolic=120, diastolic=80), text
        )
        self.assertIn(LastMeasurementMessages.PULSE.format(pulse=70), text)
        self.assertEqual(
            response.data["session"]["session_id"], payload["session"]["session_id"]
        )
        self.assertEqual(response.data["version"], payload["version"])

    def test_webhook_unauthorized_no_token(self):
        """Test that a request without a token is rejected."""
        payload = {}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_webhook_unauthorized_wrong_token(self):
        """Test that a request with a wrong token is rejected."""
        payload = {}
        response = self.client.post(
            f"{self.url}?token=wrong-secret", payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
