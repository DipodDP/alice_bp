import hashlib
import hmac
import os
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured

from alice_skill.models import AliceUser


@override_settings(TELEGRAM_ID_HMAC_KEY='test-secret-key')
class TelegramIdMigrationTest(TestCase):
    def test_migration_command(self):
        user = AliceUser.objects.create(telegram_user_id_hash='12345')
        out = StringIO()
        call_command('migrate_telegram_ids', stdout=out)

        user.refresh_from_db()
        expected_hash = hmac.new(
            b'test-secret-key',
            b'12345',
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(user.telegram_user_id_hash, expected_hash)
        self.assertIn(f'Migrated user {user.id}', out.getvalue())

    def test_migration_command_dry_run(self):
        user = AliceUser.objects.create(telegram_user_id_hash='12345')
        out = StringIO()
        call_command('migrate_telegram_ids', '--dry-run', stdout=out)

        user.refresh_from_db()
        self.assertEqual(user.telegram_user_id_hash, '12345')  # Should not have changed
        self.assertIn(f'Would migrate user {user.id}', out.getvalue())

    def test_migration_command_no_users_to_migrate(self):
        out = StringIO()
        call_command('migrate_telegram_ids', stdout=out)
        self.assertIn('No users to migrate', out.getvalue())

    def test_migration_command_already_hashed(self):
        hashed_id = hmac.new(
            b'test-secret-key',
            b'already-hashed',
            hashlib.sha256,
        ).hexdigest()
        user = AliceUser.objects.create(telegram_user_id_hash=hashed_id)

        out = StringIO()
        call_command('migrate_telegram_ids', stdout=out)

        user.refresh_from_db()
        self.assertEqual(user.telegram_user_id_hash, hashed_id)
        self.assertIn(f'Skipping user {user.id}', out.getvalue())

    @override_settings(TELEGRAM_ID_HMAC_KEY=None)
    def test_no_secret_key(self):
        AliceUser.objects.create(telegram_user_id_hash='12345')
        out = StringIO()
        call_command('migrate_telegram_ids', stdout=out)
        self.assertIn(
            'Configuration error: TELEGRAM_ID_HMAC_KEY setting is empty.',
            out.getvalue(),
        )