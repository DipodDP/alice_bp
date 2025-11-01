"""
Management command to delete expired account link tokens.

This command should be run periodically (e.g., via cron job) to prevent
database bloat from accumulating expired tokens.

Usage:
    python manage.py cleanup_expired_tokens

Or with uv:
    uv run manage.py cleanup_expired_tokens
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from alice_skill.models import AccountLinkToken


class Command(BaseCommand):
    help = 'Delete expired account link tokens from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Find all expired tokens
        expired_tokens = AccountLinkToken.objects.filter(
            expires_at__lt=timezone.now()
        )

        count = expired_tokens.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired tokens found.'))
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Would delete {count} expired token(s)'
                )
            )
            # Show sample of tokens that would be deleted
            for token in expired_tokens[:5]:
                self.stdout.write(
                    f'  - Token for Telegram user {token.telegram_user_id}, '
                    f'expired at {token.expires_at}'
                )
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more')
        else:
            deleted_count, _ = expired_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} expired token(s)'
                )
            )
