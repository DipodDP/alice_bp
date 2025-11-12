import re
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ImproperlyConfigured
from alice_skill.helpers import get_hashed_telegram_id
from alice_skill.models import AliceUser


class Command(BaseCommand):
    help = "Hashes plaintext stored in telegram_user_id_hash (in-place) to HMAC-SHA256."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulates the migration without making any changes to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        
        users_to_migrate = AliceUser.objects.filter(telegram_user_id_hash__isnull=False).exclude(telegram_user_id_hash="")
        
        if not users_to_migrate.exists():
            self.stdout.write(self.style.SUCCESS("No users to migrate."))
            return

        self.stdout.write(f"Found {users_to_migrate.count()} user(s) to migrate.")

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in dry-run mode. No changes will be made."))

        try:
            with transaction.atomic():
                # This will raise ImproperlyConfigured if not set, which is desired.
                if not settings.TELEGRAM_ID_HMAC_KEY:
                    raise ImproperlyConfigured("TELEGRAM_ID_HMAC_KEY setting is empty.")

                for user in users_to_migrate:
                    # Skip already hashed IDs (64 hex characters)
                    if user.telegram_user_id_hash and re.match(r'^[a-f0-9]{64}$', user.telegram_user_id_hash):
                        self.stdout.write(f"Skipping user {user.id} (already hashed).")
                        continue

                    original_id = user.telegram_user_id_hash
                    hashed_id = get_hashed_telegram_id(original_id)

                    if dry_run:
                        self.stdout.write(
                            f"  - Would migrate user {user.id}: '{original_id}' -> '{hashed_id}'"
                        )
                    else:
                        user.telegram_user_id_hash = hashed_id
                        user.save()
                        self.stdout.write(
                            f"  - Migrated user {user.id}: '{original_id}' -> '{hashed_id}'"
                        )
        except ImproperlyConfigured as e:
            self.stdout.write(self.style.ERROR(f"Configuration error: {e}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred during migration: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("Migration complete."))

