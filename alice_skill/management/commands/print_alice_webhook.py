from django.core.management.base import BaseCommand
from django.conf import settings
from django.urls import reverse

class Command(BaseCommand):
    help = "Prints the full Yandex.Dialogs webhook URL with the secret token."

    def handle(self, *args, **options):
        site_url = getattr(settings, "SITE_URL", None)
        alice_secret = getattr(settings, "ALICE_WEBHOOK_SECRET", None)

        if not site_url or not alice_secret:
            self.stderr.write(self.style.ERROR(
                "Error: Make sure SITE_URL and ALICE_WEBHOOK_SECRET are defined in your .env file."
            ))
            return

        # Use reverse() to get the base path for the alice-webhook
        webhook_base_path = reverse("alice-webhook")
        # Construct the full URL with the site_url and the secret token
        full_url = f"{site_url}{webhook_base_path}?token={alice_secret}"

        self.stdout.write(self.style.SUCCESS("Yandex.Dialogs Webhook URL:"))
        self.stdout.write(full_url)
