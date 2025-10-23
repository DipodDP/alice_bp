from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from alice_skill.models import AccountLinkToken
from alice_skill.services import generate_link_token, match_webhook_to_telegram_user

class WebhookMatchingLogicTest(TestCase):
    def setUp(self):
        self.telegram_user_id = 12345
        self.alice_user_id = "test_alice_user_id"
        self.token_words = ["код", "хрен", "лайм", "розмарин"]
        AccountLinkToken.objects.all().delete() # Clear tokens before each test

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_match_tokens_from_nlu_tokens_any_order(self, mock_system_random):
        """
        Tests that the matching function correctly identifies a token from nlu.tokens
        regardless of order and marks it as used.
        """
        mock_system_random.return_value.sample.return_value = self.token_words

        # Generate a token
        plaintext_token = generate_link_token(self.telegram_user_id, length=len(self.token_words))
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        self.assertFalse(AccountLinkToken.objects.first().used)

        # Simulate webhook JSON with tokens in a different order and extra words
        webhook_json = {
            "session": {"user_id": self.alice_user_id},
            "request": {"nlu": {"tokens": ["другие", "слова", "розмарин", "код", "хрен", "лайм", "еще"]}}
        }

        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        self.assertEqual(matched_telegram_user_id, self.telegram_user_id)

        # Check that the token is marked as used
        self.assertTrue(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_match_requires_all_words_present(self, mock_system_random):
        """
        Tests that the matching function does not match if not all token words are present.
        """
        mock_system_random.return_value.sample.return_value = self.token_words

        # Generate a token
        generate_link_token(self.telegram_user_id, length=len(self.token_words))

        # Simulate webhook JSON with one word missing
        webhook_json = {
            "session": {"user_id": self.alice_user_id},
            "request": {"nlu": {"tokens": ["другие", "слова", "розмарин", "код", "хрен", "еще"]}}
        }

        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        self.assertIsNone(matched_telegram_user_id)
        self.assertFalse(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_end_to_end_linking_succeeds(self, mock_system_random):
        """
        Tests the complete end-to-end flow of account linking.
        """
        mock_system_random.return_value.sample.return_value = self.token_words

        # 1. Telegram user requests token -> server stores hashed token -> returned plaintext
        plaintext_token = generate_link_token(self.telegram_user_id, length=len(self.token_words))
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        self.assertFalse(AccountLinkToken.objects.first().used)

        # 2. Webhook arrives with nlu.tokens containing token words
        webhook_json = {
            "session": {"user_id": self.alice_user_id},
            "request": {"nlu": {"tokens": plaintext_token.split()}},
            "version": "1.0"
        }

        # This part will be handled by AliceWebhookView, which needs to be updated.
        # For now, we directly call the matching function.
        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        # 3. Server links alice_user_id to telegram_user_id in linked_accounts table
        self.assertEqual(matched_telegram_user_id, self.telegram_user_id)
        self.assertTrue(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_token_expires_and_is_one_time(self, mock_system_random):
        """
        Tests that tokens expire and cannot be reused.
        """
        mock_system_random.return_value.sample.side_effect = [
            ["word1", "word2", "word3", "word4"], # For plaintext_token_expired
            ["word5", "word6", "word7", "word8"], # For plaintext_token_used (first use)
            ["word9", "word10", "word11", "word12"], # For plaintext_token_used (second use, though not used for generation)
        ]

        # --- Test 1: Token older than expiry does not match ---
        # Generate a token
        plaintext_token_expired = generate_link_token(self.telegram_user_id + 1, length=len(self.token_words))
        expired_token_obj = AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id + 1)

        # Simulate time passing beyond expiry
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = expired_token_obj.expires_at + timedelta(seconds=1)
            webhook_json_expired = {
                "session": {"user": {"user_id": "expired_alice_user"}},
                "request": {"nlu": {"tokens": plaintext_token_expired.split()}},
                "version": "1.0"
            }
            matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json_expired)
            self.assertIsNone(matched_telegram_user_id)
            self.assertFalse(AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id + 1).used)

        # --- Test 2: Token used once cannot be reused ---
        # Generate a fresh token
        plaintext_token_used = generate_link_token(self.telegram_user_id + 2, length=len(self.token_words))
        used_token_obj = AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id + 2)

        # Use the token once (simulate a successful link)
        webhook_json_first_use = {
            "session": {"user": {"user_id": "first_use_alice_user"}},
            "request": {"nlu": {"tokens": plaintext_token_used.split()}},
            "version": "1.0"
        }
        matched_telegram_user_id_first_use = match_webhook_to_telegram_user(webhook_json_first_use)
        self.assertEqual(matched_telegram_user_id_first_use, self.telegram_user_id + 2)
        self.assertTrue(AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id + 2).used)

        # Try to reuse the same token
        webhook_json_second_use = {
            "session": {"user": {"user_id": "second_use_alice_user"}},
            "request": {"nlu": {"tokens": plaintext_token_used.split()}},
            "version": "1.0"
        }
        matched_telegram_user_id_second_use = match_webhook_to_telegram_user(webhook_json_second_use)
        self.assertIsNone(matched_telegram_user_id_second_use)
        self.assertTrue(AccountLinkToken.objects.get(telegram_user_id=self.telegram_user_id + 2).used) # Still used
