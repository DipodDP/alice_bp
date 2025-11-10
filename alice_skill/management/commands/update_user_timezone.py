from django.core.management.base import BaseCommand
from alice_skill.models import AliceUser
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class Command(BaseCommand):
    help = 'Update timezone for a user by alice_user_id or telegram_user_id'

    def add_arguments(self, parser):
        parser.add_argument(
            '--alice-user-id',
            type=str,
            help='Alice user ID',
            required=False,
        )
        parser.add_argument(
            '--telegram-user-id',
            type=str,
            help='Telegram user ID',
            required=False,
        )
        parser.add_argument(
            '--timezone',
            type=str,
            required=True,
            help='Timezone to set (e.g., Asia/Krasnoyarsk, Europe/Moscow, UTC)',
        )

    def handle(self, *args, **options):
        alice_user_id = options.get('alice_user_id')
        telegram_user_id = options.get('telegram_user_id')
        timezone_str = options.get('timezone').strip()

        if not alice_user_id and not telegram_user_id:
            self.stdout.write(
                self.style.ERROR('Please provide --alice-user-id or --telegram-user-id')
            )
            return

        # Validate timezone
        try:
            ZoneInfo(timezone_str)
        except ZoneInfoNotFoundError:
            self.stdout.write(self.style.ERROR(f'Invalid timezone: {timezone_str}'))
            self.stdout.write(
                'Please use a valid IANA timezone (e.g., Asia/Krasnoyarsk, Europe/Moscow, UTC)'
            )
            return

        try:
            if alice_user_id:
                user = AliceUser.objects.get(alice_user_id=alice_user_id)
                identifier = f"alice_user_id '{alice_user_id}'"
            else:
                user = AliceUser.objects.get(telegram_user_id=telegram_user_id)
                identifier = f"telegram_user_id '{telegram_user_id}'"

            old_timezone = user.timezone
            user.timezone = timezone_str
            user.save(update_fields=['timezone'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated timezone for user with {identifier}:\n'
                    f'  Old timezone: {old_timezone}\n'
                    f'  New timezone: {timezone_str}'
                )
            )

        except AliceUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('User not found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
