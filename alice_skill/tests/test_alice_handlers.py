from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from ..models import User, LinkToken


class AliceHandlerAPITestCase(APITestCase):
    def setUp(self):
        self.alice_user_id = "TEST_ALICE_HANDLER_USER_ID"
        self.url = reverse("alice-webhook")

    def test_link_account_handler_success(self):
        """Ensure the webhook triggers the link account handler and returns a token."""
        data = {
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": "связать аккаунт с телеграмом",
                "original_utterance": "связать аккаунт с телеграмом",
            },
            "version": "1.0"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Check that the response text contains the linking message
        self.assertIn("Ваш код для связывания:", response_data["response"]["text"])
        self.assertIn("AliceBPBot", response_data["response"]["text"])

        # Check that a user and a token were created in the database
        self.assertTrue(User.objects.filter(alice_user_id=self.alice_user_id).exists())
        user = User.objects.get(alice_user_id=self.alice_user_id)
        self.assertTrue(LinkToken.objects.filter(user=user).exists())
