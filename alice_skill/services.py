import logging
import re
import secrets
import hmac
from . import messages
from .models import User, AccountLinkToken
from .wordlist import WORDLIST
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class TooManyRequests(Exception):
    pass


class TokenAlreadyUsed(Exception):
    pass


RATE_LIMIT_SECONDS = getattr(settings, "ALICE_LINK_RATE_LIMIT_SECONDS", 60)
TOKEN_LIFETIME_MINUTES = getattr(settings, "ALICE_LINK_TOKEN_LIFETIME_MINUTES", 10)


def generate_link_token(telegram_user_id: int) -> str:
    """
    Generates a unique plaintext token in the format "word-number", stores its hash in the database, and returns the plaintext token.
    The token consists of a random word from a predefined wordlist and a random 3-digit number.
    """

    # Check for rate limiting
    last_token = AccountLinkToken.objects.filter(
        telegram_user_id=telegram_user_id
    ).order_by('-created_at').first()

    if last_token and (timezone.now() - last_token.created_at).total_seconds() < RATE_LIMIT_SECONDS:
        raise TooManyRequests(messages.ServiceMessages.RATE_LIMIT_ERROR)

    random_word = secrets.SystemRandom().choice(WORDLIST)
    random_number = secrets.SystemRandom().randint(100, 999)
    plaintext_token = f"{random_word}-{random_number}"
    normalized_token = plaintext_token.lower()

    token_hash = hmac.new(
        settings.LINK_SECRET.encode(),
        normalized_token.encode(),
        'sha256'
    ).hexdigest()

    expires_at = timezone.now() + timedelta(minutes=TOKEN_LIFETIME_MINUTES)

    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=telegram_user_id,
        expires_at=expires_at,
        used=False
    )

    return plaintext_token


def _normalize_nlu_tokens(nlu_tokens: list[str]) -> list[str]:
    """
    Normalizes NLU tokens from Alice webhook by splitting, lowercasing, fixing common
    character mistakes (e.g., 'ё', Latin letters in Russian words), and cleaning them
    to contain only Cyrillic characters or digits.
    """
    normalized_tokens = []
    for token in nlu_tokens:
        sub_tokens = token.split(' ')
        for sub_token in sub_tokens:
            word = sub_token.lower().replace('ё', 'е')
            # Homoglyph replacement
            word = word.replace('a', 'а').replace('e', 'е').replace('o', 'о').replace('p', 'р').replace('c', 'с').replace('x', 'х').replace('y', 'у')

            if re.match(r'^[а-яё]+-\d{3}$', word):
                normalized_tokens.append(word)
            elif word.isdigit():
                normalized_tokens.append(word)
            else:
                cleaned_word = re.sub(r'[^а-я]', '', word)
                if cleaned_word:
                    normalized_tokens.append(cleaned_word)
    return normalized_tokens


def _generate_candidate_phrases(tokens: list[str]) -> list[str]:
    """
    Generates potential token phrases from a list of normalized tokens.
    Handles cases like: "word-123", "word 123", "word" + "123", and "word" + "1" + "2" + "3".
    """
    phrases = []
    for i, token in enumerate(tokens):
        if re.match(r'^[а-яё]+[ -]\d{3}$', token):
            phrases.append(token.replace(' ', '-'))

        if token in WORDLIST:
            if i + 1 < len(tokens) and tokens[i + 1].isdigit() and len(tokens[i + 1]) == 3:
                phrases.append(f"{token}-{tokens[i + 1]}")
            elif i + 3 < len(tokens) and all(t.isdigit() and len(t) == 1 for t in tokens[i + 1:i + 4]):
                phrases.append(f"{token}-{''.join(tokens[i + 1:i + 4])}")
    return list(set(phrases))


def match_webhook_to_telegram_user(webhook_json: dict) -> int | None:
    """
    Matches incoming Alice webhook NLU tokens against stored AccountLinkTokens.
    Returns the telegram_user_id if a match is found, otherwise None.
    This optimized version generates candidate phrases first and then performs a single DB query.
    """
    alice_user_id = webhook_json.get("session", {}).get("user_id") or webhook_json.get("session", {}).get("user", {}).get("user_id")
    if not alice_user_id:
        return None

    nlu_tokens = webhook_json.get("request", {}).get("nlu", {}).get("tokens", [])
    if not nlu_tokens:
        return None

    normalized_tokens = _normalize_nlu_tokens(nlu_tokens)
    candidate_phrases = _generate_candidate_phrases(normalized_tokens)

    if not candidate_phrases:
        return None

    candidate_hashes = [hmac.new(settings.LINK_SECRET.encode(), p.encode(), 'sha256').hexdigest() for p in candidate_phrases]

    account_link_token = AccountLinkToken.objects.filter(
        token_hash__in=candidate_hashes,
        expires_at__gt=timezone.now(),
    ).order_by('created_at').first()

    if not account_link_token:
        return None

    if account_link_token.used:
        raise TokenAlreadyUsed

    account_link_token.used = True
    account_link_token.save()

    telegram_user_id_str = str(account_link_token.telegram_user_id)

    user, _ = User.objects.get_or_create(alice_user_id=alice_user_id)
    User.objects.filter(telegram_user_id=telegram_user_id_str).exclude(pk=user.pk).update(telegram_user_id=None)
    user.telegram_user_id = telegram_user_id_str
    user.save()

    return account_link_token.telegram_user_id

