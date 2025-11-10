from django.core.management.base import BaseCommand
from alice_skill.models import AliceUser


class Command(BaseCommand):
    help = 'Check timezone for a user by alice_user_id or telegram_user_id'

    def add_arguments(self, parser):
        parser.add_argument(
            '--alice-user-id',
            type=str,
            help='Alice user ID to check',
        )
        parser.add_argument(
            '--telegram-user-id',
            type=str,
            help='Telegram user ID to check',
        )
        parser.add_argument(
            '--list-all',
            action='store_true',
            help='List all users with their timezones',
        )

    def handle(self, *args, **options):
        if options['list_all']:
            users = AliceUser.objects.all().order_by('alice_user_id')
            self.stdout.write(f'\nFound {users.count()} users:\n')
            for user in users:
                self.stdout.write(
                    f'  alice_user_id: {user.alice_user_id or "(None)"}, '
                    f'telegram_user_id: {user.telegram_user_id or "(None)"}, '
                    f"timezone: '{user.timezone}' (type: {type(user.timezone).__name__}, "
                    f'empty: {not user.timezone or user.timezone.strip() == ""})'
                )
            return

        alice_user_id = options.get('alice_user_id')
        telegram_user_id = options.get('telegram_user_id')

        if not alice_user_id and not telegram_user_id:
            self.stdout.write(
                self.style.ERROR('Please provide --alice-user-id or --telegram-user-id')
            )
            return

        try:
            if alice_user_id:
                user = AliceUser.objects.get(alice_user_id=alice_user_id)
                self.stdout.write(f"\nUser found by alice_user_id '{alice_user_id}':")
            else:
                user = AliceUser.objects.get(telegram_user_id=telegram_user_id)
                self.stdout.write(
                    f"\nUser found by telegram_user_id '{telegram_user_id}':"
                )

            self.stdout.write(f'  alice_user_id: {user.alice_user_id}')
            self.stdout.write(f'  telegram_user_id: {user.telegram_user_id}')
            self.stdout.write(f"  timezone: '{user.timezone}'")
            self.stdout.write(f'  timezone type: {type(user.timezone).__name__}')
            self.stdout.write(f'  timezone is None: {user.timezone is None}')
            self.stdout.write(f'  timezone is empty string: {user.timezone == ""}')
            self.stdout.write(
                f'  timezone is whitespace: {user.timezone.strip() == "" if user.timezone else "N/A"}'
            )
            self.stdout.write(f"  timezone or 'UTC': {user.timezone or 'UTC'}")

        except AliceUser.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
