import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import User, LinkToken

def initiate_linking_process(alice_user_id: str) -> tuple[bool, str]:
    """
    Creates a linking token for an Alice user and returns a message for them.
    Returns a tuple of (success, message).
    """
    try:
        user, _ = User.objects.get_or_create(alice_user_id=alice_user_id)

        # Generate a user-friendly, secure token
        raw_token = "".join(secrets.choice("0123456789ABCDEF") for _ in range(8))
        formatted_token = "-".join(raw_token[i:i+4] for i in range(0, len(raw_token), 4))

        # Hash the token for storage
        token_hash = hmac.new(
            settings.SECRET_KEY.encode(),
            raw_token.encode(),
            'sha256'
        ).hexdigest()

        expires_at = timezone.now() + timedelta(minutes=10)

        # Ensure only one active token exists per user
        LinkToken.objects.filter(user=user).delete()
        LinkToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at
        )

        message = (
            f"Ваш код для связывания: {formatted_token}. "
            f"Чтобы завершить, найдите в Telegram бота AliceBPBot и отправьте ему команду /link {formatted_token}"
        )
        return True, message
    except Exception as e:
        # In a real app, you'd want to log this exception
        return False, "Произошла ошибка при создании кода. Пожалуйста, попробуйте позже."
