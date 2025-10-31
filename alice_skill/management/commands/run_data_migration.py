from django.core.management.base import BaseCommand
from django.apps import apps
from alice_skill.migrations import 0004_populate_user_fk

class Command(BaseCommand):
    help = 'Runs the populate_user_fk data migration'

    def handle(self, *args, **options):
        0004_populate_user_fk.populate_user_fk(apps, None)
