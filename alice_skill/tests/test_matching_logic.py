from django.test import TestCase, override_settings
from datetime import timedelta
from unittest.mock import patch

from ..helpers import get_hashed_telegram_id
from ..models import AccountLinkToken
from ..services import (
    generate_link_token,
    match_webhook_to_telegram_user,
    TokenAlreadyUsed,
)


@override_settings(LINK_SECRET='a-super-secret-key')
class WebhookMatchingLogicTest(TestCase):
    def setUp(self):
        self.telegram_user_id = '12345'
        self.hashed_telegram_id = get_hashed_telegram_id(self.telegram_user_id)
        self.alice_user_id = 'test_alice_user_id'
        AccountLinkToken.objects.all().delete()  # Clear tokens before each test

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_match_tokens_from_nlu_tokens_any_order(self, mock_system_random):
        """
        Tests that the matching function correctly identifies a token from nlu.tokens
        regardless of order and marks it as used.
        """
        mock_system_random.return_value.choice.return_value = 'мост'
        mock_system_random.return_value.randint.return_value = 627

        # Generate a token
        generate_link_token(self.hashed_telegram_id)
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        self.assertFalse(AccountLinkToken.objects.first().used)

        # Simulate webhook JSON with tokens in a different order and extra words
        webhook_json = {
            'session': {'user_id': self.alice_user_id},
            'request': {'nlu': {'tokens': ['другие', 'слова', 'мост-627', 'еще']}},
        }

        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        self.assertEqual(matched_telegram_user_id, self.hashed_telegram_id)

        # Check that the token is marked as used
        self.assertTrue(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_match_tokens_from_nlu_tokens_split(self, mock_system_random):
        """
        Tests that the matching function correctly identifies a token from nlu.tokens
        when the word and number are split.
        """
        mock_system_random.return_value.choice.return_value = 'спаржа'
        mock_system_random.return_value.randint.return_value = 196

        # Generate a token
        generate_link_token(self.hashed_telegram_id)
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        self.assertFalse(AccountLinkToken.objects.first().used)

        # Simulate webhook JSON with tokens split
        webhook_json = {
            'session': {'user_id': self.alice_user_id},
            'request': {'nlu': {'tokens': ['свяжи', 'аккаунт', 'спаржа', '196']}},
        }

        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        self.assertEqual(matched_telegram_user_id, self.hashed_telegram_id)

        # Check that the token is marked as used
        self.assertTrue(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_end_to_end_linking_succeeds(self, mock_system_random):
        """
        Tests the complete end-to-end flow of account linking.
        """
        mock_system_random.return_value.choice.return_value = 'мост'
        mock_system_random.return_value.randint.return_value = 627

        # 1. Telegram user requests token -> server stores hashed token -> returned plaintext
        plaintext_token = generate_link_token(self.hashed_telegram_id)
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        self.assertFalse(AccountLinkToken.objects.first().used)

        # 2. Webhook arrives with nlu.tokens containing token words
        webhook_json = {
            'session': {'user_id': self.alice_user_id},
            'request': {'nlu': {'tokens': [plaintext_token]}},
            'version': '1.0',
        }

        # This part will be handled by AliceWebhookView, which needs to be updated.
        # For now, we directly call the matching function.
        matched_telegram_user_id = match_webhook_to_telegram_user(webhook_json)

        # 3. Server links alice_user_id to telegram_user_id in linked_accounts table
        self.assertEqual(matched_telegram_user_id, self.hashed_telegram_id)
        self.assertTrue(AccountLinkToken.objects.first().used)

    @patch('alice_skill.services.secrets.SystemRandom')
    def test_token_expires_and_is_one_time(self, mock_system_random):
        """
        Tests that tokens expire and cannot be reused.
        """
        mock_system_random.return_value.choice.side_effect = [
            'один',  # For plaintext_token_expired
            'пять',  # For plaintext_token_used (first use)
        ]
        mock_system_random.return_value.randint.side_effect = [
            111,  # For plaintext_token_expired
            222,  # For plaintext_token_used (first use)
        ]

        expired_user_id = '12346'
        hashed_expired_user_id = get_hashed_telegram_id(expired_user_id)
        used_user_id = '12347'
        hashed_used_user_id = get_hashed_telegram_id(used_user_id)

        # --- Test 1: Token older than expiry does not match ---
        # Generate a token
        plaintext_token_expired = generate_link_token(hashed_expired_user_id)
        expired_token_obj = AccountLinkToken.objects.get(
            telegram_user_id=hashed_expired_user_id
        )

        # Simulate time passing beyond expiry
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = expired_token_obj.expires_at + timedelta(seconds=1)
            webhook_json_expired = {
                'session': {'user_id': 'expired_alice_user'},
                'request': {'nlu': {'tokens': [plaintext_token_expired]}},
                'version': '1.0',
            }
            matched_telegram_user_id = match_webhook_to_telegram_user(
                webhook_json_expired
            )
            self.assertIsNone(matched_telegram_user_id)
            self.assertFalse(
                AccountLinkToken.objects.get(
                    telegram_user_id=hashed_expired_user_id
                ).used
            )

        # --- Test 2: Token used once cannot be reused ---
        # Generate a fresh token
        plaintext_token_used = generate_link_token(hashed_used_user_id)

        # Use the token once (simulate a successful link)
        webhook_json_first_use = {
            'session': {'user_id': 'first_use_alice_user'},
            'request': {'nlu': {'tokens': [plaintext_token_used]}},
            'version': '1.0',
        }
        matched_telegram_user_id_first_use = match_webhook_to_telegram_user(
            webhook_json_first_use
        )
        self.assertEqual(matched_telegram_user_id_first_use, hashed_used_user_id)
        self.assertTrue(
            AccountLinkToken.objects.get(telegram_user_id=hashed_used_user_id).used
        )

        # Try to reuse the same token
        webhook_json_second_use = {
            'session': {'user_id': 'second_use_alice_user'},
            'request': {'nlu': {'tokens': [plaintext_token_used]}},
            'version': '1.0',
        }
        with self.assertRaises(TokenAlreadyUsed):
            match_webhook_to_telegram_user(webhook_json_second_use)
        self.assertTrue(
            AccountLinkToken.objects.get(telegram_user_id=hashed_used_user_id).used
        )  # Still used
