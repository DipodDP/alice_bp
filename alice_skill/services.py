import secrets
import hmac
import string
import itertools
from .models import User, AccountLinkToken
from .wordlist import WORDLIST
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class TooManyRequests(Exception):
    pass

RATE_LIMIT_SECONDS = 60 # 1 minute rate limit for token generation

def generate_link_token(telegram_user_id: int, length: int = 4) -> str:
    """
    Generates a unique plaintext token, stores its hash in the database, and returns the plaintext token.
    The token consists of `length` words from a predefined wordlist.
    """

    # Check for rate limiting
    last_token = AccountLinkToken.objects.filter(
        telegram_user_id=telegram_user_id
    ).order_by('-created_at').first()

    if last_token and (timezone.now() - last_token.created_at).total_seconds() < RATE_LIMIT_SECONDS:
        raise TooManyRequests("Too many token generation requests for this user.")

    # Generate a token phrase from the wordlist
    token_words = secrets.SystemRandom().sample(WORDLIST, k=length)
    plaintext_token = " ".join(token_words)

    # Normalize the token for hashing (lowercase, join with single space, sorted words)
    normalized_token = " ".join(sorted(token_words)).lower()

    # Hash the token for storage
    token_hash = hmac.new(
        settings.LINK_SECRET.encode(),
        normalized_token.encode(),
        'sha256'
    ).hexdigest()
    print(f"DEBUG: generate_link_token saving token_hash: {token_hash}")

    expires_at = timezone.now() + timedelta(minutes=10) # Configurable lifetime

    # Store the hashed token and metadata
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=telegram_user_id,
        token_word_count=length,
        expires_at=expires_at,
        used=False
    )
    created_token = AccountLinkToken.objects.get(token_hash=token_hash)

    return plaintext_token

def match_webhook_to_telegram_user(webhook_json: dict) -> int | None:
    """
    Matches incoming Alice webhook NLU tokens against stored AccountLinkTokens.
    Returns the telegram_user_id if a match is found, otherwise None.
    """
    alice_user_id = webhook_json.get("session", {}).get("user_id")
    if not alice_user_id:
        alice_user_id = webhook_json.get("session", {}).get("user", {}).get("user_id")
    if not alice_user_id:
        return None

    nlu_tokens = webhook_json.get("request", {}).get("nlu", {}).get("tokens", [])
    if not nlu_tokens:
        return None
    
    # Normalize NLU tokens: lowercase and remove punctuation
    normalized_nlu_tokens = [
        word.lower().strip(string.punctuation) for word in nlu_tokens
    ]
    normalized_nlu_tokens = [word for word in normalized_nlu_tokens if word] # Remove empty strings

    current_time = timezone.now()
    active_tokens = AccountLinkToken.objects.filter(
        used=False,
        expires_at__gt=current_time
    )

    for account_link_token in active_tokens:
        expected_word_count = account_link_token.token_word_count

        # Generate combinations of NLU tokens that match the expected word count
        # Use combinations and sort the words within each combination to ensure order does not matter for hashing
        for combo in itertools.combinations(normalized_nlu_tokens, expected_word_count):
            candidate_token_phrase = " ".join(sorted(combo)) # Sort for consistent hashing
            candidate_token_hash = hmac.new(
                settings.LINK_SECRET.encode(),
                candidate_token_phrase.encode(),
                'sha256'
            ).hexdigest()

            if candidate_token_hash == account_link_token.token_hash:
                # Found a match!
                account_link_token.used = True
                account_link_token.save()

                # Find or create User and link Alice ID
                user, created = User.objects.get_or_create(
                    telegram_user_id=account_link_token.telegram_user_id
                )
                user.alice_user_id = alice_user_id
                user.save()

                return account_link_token.telegram_user_id

    return None
