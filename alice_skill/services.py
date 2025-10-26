import logging
import re
import secrets
import hmac
import itertools
from . import messages
from .models import User, AccountLinkToken
from .wordlist import WORDLIST
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class TooManyRequests(Exception):
    pass

RATE_LIMIT_SECONDS = 60 # 1 minute rate limit for token generation

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

    # Generate a random word from the wordlist
    random_word = secrets.SystemRandom().choice(WORDLIST)
    # Generate a random 3-digit number
    random_number = secrets.SystemRandom().randint(100, 999)

    plaintext_token = f"{random_word}-{random_number}"

    # Normalize the token for hashing (lowercase)
    normalized_token = plaintext_token.lower()

    # Hash the token for storage
    token_hash = hmac.new(
        settings.LINK_SECRET.encode(),
        normalized_token.encode(),
        'sha256'
    ).hexdigest()

    expires_at = timezone.now() + timedelta(minutes=10) # Configurable lifetime

    # Store the hashed token and metadata
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=telegram_user_id,
        expires_at=expires_at,
        used=False
    )

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
    
    # Normalize NLU tokens
    normalized_nlu_tokens = []
    for token in nlu_tokens:
        word = token.lower()
        word = word.replace('ё', 'е')
        word = word.replace('a', 'а').replace('e', 'е').replace('o', 'о').replace('p', 'р').replace('c', 'с').replace('x', 'х').replace('y', 'у')
        
        # Keep the original token if it matches the word-number pattern
        if re.match(r'^[а-яё]+-\d{3}$', word):
            normalized_nlu_tokens.append(word)
        elif word.isdigit(): # Keep purely numeric tokens
            normalized_nlu_tokens.append(word)
        else:
            # Otherwise, remove non-Cyrillic characters and append if not empty
            cleaned_word = re.sub(r'[^а-я]', '', word)
            if cleaned_word:
                normalized_nlu_tokens.append(cleaned_word)

    current_time = timezone.now()
    active_tokens = AccountLinkToken.objects.filter(
        used=False,
        expires_at__gt=current_time
    )

    for account_link_token in active_tokens:
        for i, nlu_token in enumerate(normalized_nlu_tokens):
            candidate_token_phrase = None
            # Check if the current token is a word from our wordlist
            if nlu_token in WORDLIST:
                # Look for a number immediately following the word
                if i + 1 < len(normalized_nlu_tokens) and normalized_nlu_tokens[i+1].isdigit():
                    candidate_token_phrase = f"{nlu_token}-{normalized_nlu_tokens[i+1]}"
                # If the word itself is the token (e.g., 'горох-882' was not split)
                elif re.match(r'^[а-яё]+-\d{3}$', nlu_token):
                    candidate_token_phrase = nlu_token
            # If the token is already in 'word-number' format
            elif re.match(r'^[а-яё]+-\d{3}$', nlu_token):
                candidate_token_phrase = nlu_token
            
            if candidate_token_phrase:
                candidate_token_hash = hmac.new(
                    settings.LINK_SECRET.encode(),
                    candidate_token_phrase.encode(),
                    'sha256'
                ).hexdigest()

                if candidate_token_hash == account_link_token.token_hash:
                    # Found a match!
                    account_link_token.used = True
                    account_link_token.save()

                    telegram_user_id_str = str(account_link_token.telegram_user_id)

                    # Find or create the user based on the Alice ID
                    user, created = User.objects.get_or_create(alice_user_id=alice_user_id)

                    # Clear any existing user's telegram_user_id if it matches the new one
                    User.objects.filter(telegram_user_id=telegram_user_id_str).exclude(pk=user.pk).update(telegram_user_id=None)

                    user.telegram_user_id = telegram_user_id_str
                    user.save()

                    return account_link_token.telegram_user_id

    return None
