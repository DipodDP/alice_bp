import io
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth.models import User as DjangoUser
from django.utils import timezone
from datetime import timedelta
from alice_skill.models import AliceUser, AccountLinkToken


class TestManagementCommands(TestCase):
    def setUp(self):
        self.django_user1 = DjangoUser.objects.create_user(username='test_user1', password='testpassword')
        self.alice_user1 = AliceUser.objects.create(
            user=self.django_user1,
            alice_user_id="alice_user_1",
            telegram_user_id_hash="telegram_user_1",
            timezone="Europe/Moscow"
        )

        self.django_user2 = DjangoUser.objects.create_user(username='test_user2', password='testpassword')
        self.alice_user2 = AliceUser.objects.create(
            user=self.django_user2,
            alice_user_id="alice_user_2",
            telegram_user_id_hash="telegram_user_2",
            timezone="Asia/Krasnoyarsk"
        )

    def test_check_user_timezone_by_alice_id(self):
        out = io.StringIO()
        call_command('check_user_timezone', '--alice-user-id', self.alice_user1.alice_user_id, stdout=out)
        self.assertIn("User found by alice_user_id", out.getvalue())
        self.assertIn("Europe/Moscow", out.getvalue())

    def test_check_user_timezone_by_telegram_id(self):
        out = io.StringIO()
        call_command('check_user_timezone', '--telegram-user-id-hash', self.alice_user2.telegram_user_id_hash, stdout=out)
        self.assertIn("User found by telegram_user_id_hash", out.getvalue())
        self.assertIn("Asia/Krasnoyarsk", out.getvalue())

    def test_check_user_timezone_list_all(self):
        out = io.StringIO()
        call_command('check_user_timezone', '--list-all', stdout=out)
        self.assertIn("Found 2 users", out.getvalue())
        self.assertIn("alice_user_1", out.getvalue())
        self.assertIn("telegram_user_1", out.getvalue())
        self.assertIn("Europe/Moscow", out.getvalue())
        self.assertIn("alice_user_2", out.getvalue())
        self.assertIn("telegram_user_2", out.getvalue())
        self.assertIn("Asia/Krasnoyarsk", out.getvalue())

    def test_check_user_timezone_no_args(self):
        out = io.StringIO()
        call_command('check_user_timezone', stdout=out)
        self.assertIn("Please provide --alice-user-id or --telegram-user-id", out.getvalue())

    def test_check_user_timezone_not_found(self):
        out = io.StringIO()
        call_command('check_user_timezone', '--alice-user-id', 'non-existing-user', stdout=out)
        self.assertIn("User not found", out.getvalue())

    def test_update_user_timezone_by_alice_id(self):
        out = io.StringIO()
        call_command(
            'update_user_timezone',
            '--alice-user-id',
            self.alice_user1.alice_user_id,
            '--timezone',
            'America/New_York',
            stdout=out
        )
        self.assertIn("Successfully updated timezone", out.getvalue())
        self.alice_user1.refresh_from_db()
        self.assertEqual(self.alice_user1.timezone, "America/New_York")

    def test_update_user_timezone_by_telegram_id(self):
        out = io.StringIO()
        call_command(
            'update_user_timezone',
            '--telegram-user-id-hash',
            self.alice_user2.telegram_user_id_hash,
            '--timezone',
            'UTC',
            stdout=out
        )
        self.assertIn("Successfully updated timezone", out.getvalue())
        self.alice_user2.refresh_from_db()
        self.assertEqual(self.alice_user2.timezone, "UTC")

    def test_update_user_timezone_invalid_timezone(self):
        out = io.StringIO()
        call_command(
            'update_user_timezone',
            '--alice-user-id',
            self.alice_user1.alice_user_id,
            '--timezone',
            'Invalid/Timezone',
            stdout=out
        )
        self.assertIn("Invalid timezone", out.getvalue())
        self.alice_user1.refresh_from_db()
        self.assertEqual(self.alice_user1.timezone, "Europe/Moscow")

    def test_update_user_timezone_not_found(self):
        out = io.StringIO()
        call_command(
            'update_user_timezone',
            '--alice-user-id',
            'non-existing-user',
            '--timezone',
            'UTC',
            stdout=out
        )
        self.assertIn("User not found", out.getvalue())

    def test_cleanup_expired_tokens(self):
        AccountLinkToken.objects.create(
            telegram_user_id_hash="1",
            token_hash="1",
            expires_at=timezone.now() - timedelta(hours=1)
        )
        AccountLinkToken.objects.create(
            telegram_user_id_hash="2",
            token_hash="2",
            expires_at=timezone.now() + timedelta(hours=1)
        )
        out = io.StringIO()
        call_command('cleanup_expired_tokens', stdout=out)
        self.assertIn("Successfully deleted 1 expired token(s)", out.getvalue())
        self.assertEqual(AccountLinkToken.objects.count(), 1)

    def test_cleanup_expired_tokens_no_expired(self):
        AccountLinkToken.objects.create(
            telegram_user_id_hash="1",
            token_hash="1",
            expires_at=timezone.now() + timedelta(hours=1)
        )
        out = io.StringIO()
        call_command('cleanup_expired_tokens', stdout=out)
        self.assertIn("No expired tokens found", out.getvalue())
        self.assertEqual(AccountLinkToken.objects.count(), 1)

    def test_cleanup_expired_tokens_dry_run(self):
        AccountLinkToken.objects.create(
            telegram_user_id_hash="1",
            token_hash="1",
            expires_at=timezone.now() - timedelta(hours=1)
        )
        out = io.StringIO()
        call_command('cleanup_expired_tokens', '--dry-run', stdout=out)
        self.assertIn("[DRY RUN] Would delete 1 expired token(s)", out.getvalue())
        self.assertEqual(AccountLinkToken.objects.count(), 1)