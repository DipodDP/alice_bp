from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from alice_skill.helpers import get_hashed_telegram_id
from alice_skill.models import AccountLinkToken
from alice_skill.services import generate_link_token, TooManyRequests


@override_settings(LINK_SECRET='a-super-secret-key')
class AccountLinkTokenModelTest(TestCase):
    def test_token_model_schema_exists(self):
        """
        Tests that the AccountLinkToken model exists with the correct fields.
        """
        # The model is imported at the top, so if it doesn't exist, an ImportError would occur there.
        # We just need to check the fields.
        fields = [field.name for field in AccountLinkToken._meta.get_fields()]
        self.assertIn('id', fields)
        self.assertIn('token_hash', fields)
        self.assertIn('telegram_user_id_hash', fields)
        self.assertIn('created_at', fields)
        self.assertIn('expires_at', fields)
        self.assertIn('used', fields)

    @patch('alice_skill.services.secrets.SystemRandom')
    @patch('alice_skill.services.hmac.new')
    def test_generate_token_creates_hash_and_record(
        self, mock_hmac_new, mock_system_random
    ):
        """
        Tests that generate_link_token returns a plaintext token and stores a hashed record.
        """
        mock_system_random.return_value.choice.return_value = 'мост'
        mock_system_random.return_value.randint.return_value = 627
        mock_hmac_new.return_value.hexdigest.return_value = 'hashedtoken123'

        telegram_user_id = '12345'
        hashed_telegram_id = get_hashed_telegram_id(telegram_user_id)

        plaintext_token = generate_link_token(telegram_user_id)

        self.assertEqual(plaintext_token, 'мост-627')

        # Check that a record was created in the database
        self.assertEqual(AccountLinkToken.objects.count(), 1)
        stored_token = AccountLinkToken.objects.first()

        self.assertEqual(stored_token.token_hash, 'hashedtoken123')
        self.assertEqual(stored_token.telegram_user_id_hash, hashed_telegram_id)
        self.assertFalse(stored_token.used)
        self.assertLess(timezone.now() - stored_token.created_at, timedelta(seconds=5))
        self.assertGreater(stored_token.expires_at, timezone.now())

    @patch('alice_skill.services.secrets.SystemRandom')
    @patch('alice_skill.services.get_hashed_telegram_id')
    @patch('alice_skill.services.hmac.new')
    def test_rate_limit_and_uniqueness(self, mock_hmac_new, mock_get_hashed_telegram_id, mock_system_random):
        """
        Tests that generating tokens too frequently for the same user raises TooManyRequests
        and that simultaneous requests yield distinct tokens.
        """
        mock_hmac_new.return_value.hexdigest.side_effect = ['hash1', 'hash2', 'hash3', 'hash4'] # Added more side effects
        mock_system_random.return_value.choice.side_effect = ['word1', 'word3', 'word5']
        mock_system_random.return_value.randint.side_effect = [123, 456, 789]

        telegram_user_id = '67890'
        hashed_telegram_id = 'hashed_67890' # Mock the hashed ID
        mock_get_hashed_telegram_id.return_value = hashed_telegram_id

        # First token generation should succeed
        token1 = generate_link_token(telegram_user_id)
        self.assertEqual(token1, 'word1-123')
        self.assertEqual(AccountLinkToken.objects.count(), 1)

        # Simulate time passing, but not enough for rate limit reset
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = timezone.make_aware(
                timezone.datetime(2025, 10, 22, 10, 0, 0)
            ) + timedelta(seconds=5)
            # Second token generation for the same user should raise TooManyRequests
            with self.assertRaises(TooManyRequests):
                generate_link_token(telegram_user_id)