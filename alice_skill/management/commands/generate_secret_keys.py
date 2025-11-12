import secrets
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key


class Command(BaseCommand):
    help = 'Generates new secret keys for the application'

    def handle(self, *args, **options):
        keys = {
            'SECRET_KEY': get_random_secret_key(),
            'ALICE_WEBHOOK_SECRET': secrets.token_hex(32),
            'LINK_SECRET': secrets.token_hex(32),
            'TELEGRAM_ID_HMAC_KEY': secrets.token_hex(32),
            'BOT_WEBHOOK_SECRET': secrets.token_hex(32),
        }

        self.stdout.write(
            self.style.SUCCESS('Generated secret keys:')
        )
        for name, key in keys.items():
            self.stdout.write(f'{name}={key}')
        self.stdout.write(
            self.style.WARNING(
                '\nAdd these to your .env file or environment variables.'
            )
        )