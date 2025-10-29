from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

from ..messages import LinkAccountMessages


from ..models import User, AccountLinkToken
from ..services import generate_link_token


@override_settings(ALICE_WEBHOOK_SECRET="test-secret")
class AliceHandlerAPITestCase(APITestCase):
    def setUp(self):
        self.alice_user_id = "TEST_ALICE_HANDLER_USER_ID"
        self.telegram_user_id = 12345
        self.url = reverse("alice-webhook")
        self.token = "test-secret"

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

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

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

    @patch("alice_skill.services.secrets.SystemRandom")
    def test_link_account_handler_success_with_space_in_token(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and successfully links accounts
        when the token has a space instead of a hyphen.
        """
        mock_system_random.return_value.choice.return_value = "инжир"
        mock_system_random.return_value.randint.return_value = 788

        # 1. Generate a token (simulating Telegram bot generating it)
        plaintext_token_hyphen = generate_link_token(self.telegram_user_id) # e.g., "инжир-788"
        plaintext_token_space = plaintext_token_hyphen.replace('-', ' ') # e.g., "инжир 788"

        # 2. Simulate Alice webhook with NLU tokens containing the generated token with a space
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"свяжи аккаунт {plaintext_token_space}",
                "original_utterance": f"свяжи аккаунт {plaintext_token_space}",
                "nlu": {"tokens": ["свяжи", "аккаунт", plaintext_token_space]},
            },
            "version": "1.0",
        }

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

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

    @patch("alice_skill.services.secrets.SystemRandom")
    def test_link_account_handler_success_with_split_number_tokens(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and successfully links accounts
        when the three-digit number is split into individual digit tokens.
        """
        mock_system_random.return_value.choice.return_value = "гвоздика"
        mock_system_random.return_value.randint.return_value = 857

        # 1. Generate a token (simulating Telegram bot generating it)
        plaintext_token_hyphen = generate_link_token(self.telegram_user_id) # e.g., "гвоздика-857"
        word, number = plaintext_token_hyphen.split('-')

        # 2. Simulate Alice webhook with NLU tokens containing the split number
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"свяжи аккаунт код {word} {' '.join(list(number))}",
                "original_utterance": f"свяжи аккаунт код {word} {' '.join(list(number))}",
                "nlu": {"tokens": ["свяжи", "аккаунт", "код", word, *list(number)]},
            },
            "version": "1.0",
        }

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

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

    @patch("alice_skill.services.secrets.SystemRandom")
    def test_link_account_handler_success_without_trigger_phrase(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and successfully links accounts
        when only the linking code is provided, without a trigger phrase.
        """
        mock_system_random.return_value.choice.return_value = "укроп"
        mock_system_random.return_value.randint.return_value = 853

        # 1. Generate a token (simulating Telegram bot generating it)
        plaintext_token_hyphen = generate_link_token(self.telegram_user_id) # e.g., "укроп-853"
        word, number = plaintext_token_hyphen.split('-')

        # 2. Simulate Alice webhook with NLU tokens containing the code only
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"код {word} {number}",
                "original_utterance": f"код {word} {number}",
                "nlu": {"tokens": ["код", word, number]},
            },
            "version": "1.0",
        }

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

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

    @patch("alice_skill.services.secrets.SystemRandom")
    def test_link_account_handler_used_token(self, mock_system_random):
        """
        Ensure the webhook triggers the link account handler and returns an error
        when the token has already been used.
        """
        mock_system_random.return_value.choice.return_value = "виноград"
        mock_system_random.return_value.randint.return_value = 122

        # 1. Generate a token and mark it as used
        plaintext_token = generate_link_token(self.telegram_user_id)
        account_link_token = AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id)
        account_link_token.used = True
        account_link_token.save()

        # 2. Simulate Alice webhook with NLU tokens containing the used code
        data = {
            "meta": {"timezone": "UTC"},
            "session": {
                "session_id": "test-session",
                "user_id": self.alice_user_id,
            },
            "request": {
                "command": f"код {plaintext_token}",
                "original_utterance": f"код {plaintext_token}",
                "nlu": {"tokens": ["код", "виноград", "122"]},
            },
            "version": "1.0",
        }

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # Check that the response text indicates failure due to used token
        self.assertIn(LinkAccountMessages.FAIL, response_data["response"]["text"])

        # Ensure no new AccountLink record is created or existing one is changed
        self.assertFalse(
            User.objects.filter(
                alice_user_id=self.alice_user_id, telegram_user_id=self.telegram_user_id
            ).exists()
        )

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

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn(LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS, response_data["response"]["text"])

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

        response = self.client.post(f"{self.url}?token={self.token}", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        # The LinkAccountHandler should be triggered and return the no-token message
        self.assertIn(LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS, response_data["response"]["text"])
