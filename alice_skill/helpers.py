import re
from datetime import datetime
from zoneinfo import ZoneInfo

from .messages import DateFormattingMessages


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
        # Replace Latin lookalikes (basic set)
        word = (
            word.replace("a", "а")
            .replace("e", "е")
            .replace("o", "о")
            .replace("p", "р")
            .replace("c", "с")
            .replace("x", "х")
            .replace("y", "у")
        )
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
