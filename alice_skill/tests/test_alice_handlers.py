from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from ..models import User, AccountLinkToken
from ..services import generate_link_token


class AliceHandlerAPITestCase(APITestCase):
    def setUp(self):
        self.alice_user_id = "TEST_ALICE_HANDLER_USER_ID"
        self.telegram_user_id = 12345
        self.url = reverse("alice-webhook")
        self.token_words = ["код", "хрен", "лайм", "розмарин"]

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_link_account_handler_success(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and successfully links accounts.
        """
        mock_system_random.return_value.sample.return_value = self.token_words

        # 1. Generate a token (simulating Telegram bot generating it)
        plaintext_token = generate_link_token(self.telegram_user_id, length=len(self.token_words))

        # 2. Simulate Alice webhook with NLU tokens containing the generated token words
        data = {
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"связать аккаунт {plaintext_token}",
                "original_utterance": f"связать аккаунт {plaintext_token}",
                "nlu": {"tokens": plaintext_token.split()},
            },
            "version": "1.0"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Check that the response text indicates successful linking
        self.assertIn("Аккаунты успешно связаны!", response_data["response"]["text"])

        # Check that the AccountLinkToken is marked as used
        account_link_token = AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id)
        self.assertTrue(account_link_token.used)

        # Check that an AccountLink record is created
        self.assertTrue(User.objects.filter(alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id).exists())
