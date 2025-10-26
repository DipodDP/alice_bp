from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from ..messages import LinkAccountMessages


from ..models import User, AccountLinkToken
from ..services import generate_link_token


class AliceHandlerAPITestCase(APITestCase):
    def setUp(self):
        self.alice_user_id = "TEST_ALICE_HANDLER_USER_ID"
        self.telegram_user_id = 12345
        self.url = reverse("alice-webhook")

    @patch("alice_skill.services.secrets.SystemRandom")
    def test_link_account_handler_success(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and successfully links accounts.
        """
        mock_system_random.return_value.choice.return_value = "мост"
        mock_system_random.return_value.randint.return_value = 627

        # 1. Generate a token (simulating Telegram bot generating it)
        plaintext_token = generate_link_token(self.telegram_user_id)

        # 2. Simulate Alice webhook with NLU tokens containing the generated token
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"свяжи аккаунт {plaintext_token}",
                "original_utterance": f"свяжи аккаунт {plaintext_token}",
                "nlu": {"tokens": ["свяжи", "аккаунт", plaintext_token]},
            },
            "version": "1.0",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Check that the response text indicates successful linking
        self.assertIn(LinkAccountMessages.SUCCESS, response_data["response"]["text"])

        # Check that the AccountLinkToken is marked as used
        account_link_token = AccountLinkToken.objects.get(
            telegram_user_id=self.telegram_user_id
        )
        self.assertTrue(account_link_token.used)

        # Check that an AccountLink record is created

    def test_link_account_handler_no_token(self):
        """
        Ensure the webhook triggers the link account handler and returns the correct response when no token is provided.
        """
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": "свяжи аккаунт",
                "original_utterance": "свяжи аккаунт",
                "nlu": {"tokens": ["свяжи", "аккаунт"]},
            },
            "version": "1.0",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn(LinkAccountMessages.FAIL, response_data["response"]["text"])

        # Check that no AccountLink record is created
        self.assertFalse(
            User.objects.filter(
                alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id
            ).exists()
        )

    def test_get_original_utterance_normalization(self):
        """
        Ensure that get_original_utterance normalizes Latin look-alike characters.
        """
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": "cвяжи аккаунт",  # Latin 'c'
                "original_utterance": "cвяжи аккаунт",  # Latin 'c'
                "nlu": {"tokens": ["cвяжи", "аккаунт"]},
            },
            "version": "1.0",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # The LinkAccountHandler should be triggered and return the no-token message
        self.assertIn(LinkAccountMessages.FAIL, response_data["response"]["text"])
