import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .messages import DateFormattingMessages
from .models import AliceUser

logger = logging.getLogger(__name__)


def get_user_context(request):
    """
    Adds user and timezone information to the serializer context.
    """
    context = {}
    user = request.user
    is_bot_request = getattr(request, 'is_bot', False)

    # For authenticated users, add their AliceUser and timezone to the context
    if user.is_authenticated:
        try:
            alice_user = AliceUser.objects.select_related('user').get(user=user)
            context['alice_user'] = alice_user
            context['timezone'] = alice_user.timezone or 'UTC'
        except AliceUser.DoesNotExist:
            pass  # No linked AliceUser, so no user-specific context is added

    # For bot requests, find the user by user_id and add their info to the context
    elif is_bot_request:
        user_id = request.query_params.get('user_id')
        if user_id:
            try:
                alice_user = AliceUser.objects.get(alice_user_id=user_id)
                context['alice_user'] = alice_user
                context['timezone'] = alice_user.timezone or 'UTC'
                logger.debug(
                    f"Bot request: Found user {user_id} with timezone '{alice_user.timezone}'"
                )
            except AliceUser.DoesNotExist:
                logger.warning(
                    f"Bot request: User with alice_user_id '{user_id}' not found"
                )

    return context



def replace_latin_homoglyphs(text: str) -> str:
    """
    Replaces Latin characters that look like Cyrillic with their Cyrillic equivalents.
    This handles common ASR errors where Latin characters are confused with Cyrillic.

    Args:
        text: Input string that may contain Latin homoglyphs

    Returns:
        String with Latin homoglyphs replaced by Cyrillic characters
    """
    return (
        text.replace('a', 'а')
        .replace('e', 'е')
        .replace('o', 'о')
        .replace('p', 'р')
        .replace('c', 'с')
        .replace('x', 'х')
        .replace('y', 'у')
    )


def normalize_spoken_token(tokens: list[str]) -> str:
    """
    Normalizes a list of spoken tokens into a canonical three-word string.
    - Lowercases all tokens.
    - Removes punctuation and extra spaces.
    - Replaces 'ё' with 'е'.
    - Replaces common Latin lookalike characters with Cyrillic equivalents.
    """
    normalized_words = []
    for token in tokens:
        # Lowercase
        word = token.lower()
        # Replace 'ё' with 'е'
        word = word.replace("ё", "е")
        # Replace Latin lookalikes using utility function
        word = replace_latin_homoglyphs(word)
        # Remove all non-Cyrillic characters (including punctuation, numbers, etc.)
        word = re.sub(r"[^а-я]", "", word)
        if word:
            normalized_words.append(word)
    return " ".join(normalized_words).strip()


def format_measured_at(
    measured_at_str: str, user_tz_str: str, current_time: datetime
) -> str:
    measured_at = datetime.fromisoformat(measured_at_str.replace("Z", "+00:00"))

    user_tz = ZoneInfo(user_tz_str)

    measured_at_local = measured_at.astimezone(user_tz)
    now_local = current_time.astimezone(user_tz)

    today = now_local.date()
    measured_date = measured_at_local.date()
    delta = today - measured_date

    if delta.days == 0:
        date_str = DateFormattingMessages.TODAY
    elif delta.days == 1:
        date_str = DateFormattingMessages.YESTERDAY
    elif delta.days == 2:
        date_str = DateFormattingMessages.DAY_BEFORE_YESTERDAY
    else:
        date_str = measured_at_local.strftime("%d.%m.%Y")

    time_str = measured_at_local.strftime("%H:%M")
    return f"{date_str} {DateFormattingMessages.PREPOSITION} {time_str}"


def build_alice_response_payload(text, request_data):
    session_data = request_data["session"]
    return {
        "response": {"text": text, "end_session": False},
        "session": {
            "session_id": session_data["session_id"],
            "user_id": session_data["user_id"],
        },
        "version": request_data["version"],
    }
