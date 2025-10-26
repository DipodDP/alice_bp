import pytest
import json
import hmac
import hashlib
from datetime import timedelta
from django.utils import timezone
from ..messages import LinkAccountMessages
from ..models import AccountLinkToken, User

# Mock settings for testing


@pytest.fixture
def secret():
    return "a-super-secret-key"


@pytest.fixture
def create_token_hash(secret):
    def _create_token_hash(token_norm):
        return hmac.new(
            secret.encode("utf-8"), token_norm.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    return _create_token_hash


@pytest.fixture
def alice_webhook_payload(session_id="test-session", message_id=1, user_id="test-user"):
    def _payload(nlu_tokens=None, original_utterance="", command="", user_id=user_id):
        payload = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "Europe/Moscow",
                "client_id": "ru.yandex.searchplugin/7.16 (lge Nexus 5X; Android 8.1.0)",
                "interfaces": {"screen": {}, "payments": {}, "account_linking": {}},
            },
            "session": {
                "message_id": message_id,
                "session_id": session_id,
                "skill_id": "test-skill-id",
                "user_id": user_id,
                "new": False,
            },
            "request": {
                "command": command,
                "original_utterance": original_utterance,
                "type": "SimpleUtterance",
                "nlu": {
                    "tokens": nlu_tokens if nlu_tokens is not None else [],
                    "entities": [],
                },
            },
            "version": "1.0",
        }
        return payload

    return _payload


# Iteration 0 - Smoke Tests (failing)


def test_smoke_valid_token_nlu_tokens_fails(
    client, db, create_token_hash, alice_webhook_payload
):
    """
    Test A: Send payload with valid token in nlu.tokens.
    Expects successful linking, but current handler should fail.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт мост белый дом",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_smoke_invalid_token_nlu_tokens_fails(
    client, db, create_token_hash, alice_webhook_payload
):
    """
    Test B: Send payload with invalid token in nlu.tokens (not in DB).
    Expects failure (original error message).
    """
    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт", "не", "существующий", "токен"],
        original_utterance="связать аккаунт не существующий токен",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.FAIL in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert not AccountLinkToken.objects.filter(
        token_hash=create_token_hash(" ".join(sorted(["не", "существующий", "токен"])))
    ).exists()


@pytest.fixture
def normalize_spoken_token_func():
    # This fixture will provide the function once it's implemented in helpers.py
    from alice_skill.helpers import normalize_spoken_token

    return normalize_spoken_token


def test_normalize_spoken_token_basic(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["мост", "белый", "дом"]) == "мост белый дом"


def test_normalize_spoken_token_uppercase(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["МОСТ", "БЕЛЫЙ", "ДОМ"]) == "мост белый дом"


def test_normalize_spoken_token_latin_lookalikes(normalize_spoken_token_func):
    # Example: 'c' (Latin) -> 'с' (Cyrillic)
    assert normalize_spoken_token_func(["cтоп", "в", "пути"]) == "стоп в пути"


def test_normalize_spoken_token_punctuation_hyphen(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["мост-", "белый.", "дом!"]) == "мост белый дом"


def test_normalize_spoken_token_empty_list(normalize_spoken_token_func):
    assert normalize_spoken_token_func([]) == ""


def test_normalize_spoken_token_single_word(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["слово"]) == "слово"


def test_normalize_spoken_token_multiple_spaces(normalize_spoken_token_func):
    assert (
        normalize_spoken_token_func(["  мост  ", "  белый  ", "  дом  "])
        == "мост белый дом"
    )


def test_normalize_spoken_token_yo_to_e(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["ёлка", "мёд", "пёс"]) == "елка мед пес"


def test_iteration2_nlu_tokens_primary_extraction(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: when nlu.tokens = ["мост","белый","дом"], handler calls normalize_spoken_token,
    computes token_hash = HMAC(SECRET, token_norm), and finds the matching token row in DB.
    Expected: Alice JSON with "text":"Аккаунты связаны. Спасибо!", HTTP 200, and DB: link_tokens.used == true.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт мост белый дом",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )

    assert response.status_code == 200
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_iteration3_nlu_tokens_fragmented(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: nlu.tokens might be ["мост","бел","ый","дом"] or include noise tokens;
    implement logic to find the best consecutive sequence of three valid Russian-word tokens.
    Expect success when three-word sequence present.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    # Case 1: Fragmented tokens
    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт", "какой-то", "шум"]
        + token_words
        + ["еще", "слова"],
        original_utterance="связать аккаунт какой-то шум мост белый дом еще слова",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_iteration3_nlu_tokens_no_valid_triple(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: nlu.tokens does not contain a valid three-word sequence.
    Expects failure (original error message).
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт", "один", "два", "четыре"],
        original_utterance="связать аккаунт один два четыре",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.FAIL in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is False


def test_iteration5_advanced_asr_morphological_variants(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: nlu.tokens contains morphological variants, but normalization should still match.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    # Morphological variants (e.g., different endings)
    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт мост белый дом",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_iteration5_advanced_asr_extra_words_and_punctuation(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: nlu.tokens contains extra words and punctuation, but the core triple should be recovered.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    # Extra words and punctuation
    payload = alice_webhook_payload(
        nlu_tokens=[
            "связать",
            "аккаунт",
            "пожалуйста",
            "скажи",
            "мост,",
            "белый",
            "дом!",
            "спасибо",
        ],
        original_utterance="связать аккаунт пожалуйста скажи мост, белый дом! спасибо",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_iteration5_advanced_asr_no_match_after_normalization(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: nlu.tokens contains words that, even after normalization, do not form a valid triple.
    Expects failure.
    """
    token_words = ["мост", "белый", "дом"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт", "один", "два", "четыре", "пять"],
        original_utterance="связать аккаунт один два четыре пять",
    )
    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.FAIL in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is False


def test_iteration4_token_one_time_use(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: Attempt to reuse the same token twice.
    First call: success. Second call: failure with message "token already used".
    """
    token_words = ["один", "два", "три"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт один два три",
        user_id="user-first-try",
    )

    # First attempt: should succeed
    response1 = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data1 = response1.json()

    assert response1.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data1["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True
    assert (
        User.objects.get(telegram_user_id=str(12345)).alice_user_id == "user-first-try"
    )

    # Second attempt with the same token: should fail
    payload_second = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт один два три",
        user_id="user-second-try",
    )
    response2 = client.post(
        "/alice_webhook/", json.dumps(payload_second), content_type="application/json"
    )
    response_data2 = response2.json()

    assert response2.status_code == 200
    assert LinkAccountMessages.FAIL in response_data2["response"]["text"]
    assert "Аккаунты связаны" not in response_data2["response"]["text"]
    # Ensure the token remains used=True and linked to the first user
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_link_account_handler_update_telegram_user_id(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: If an Alice user already exists and is linked to a Telegram user,
    linking them to a new Telegram user should update the telegram_user_id for that Alice user.
    """
    # 1. Create an existing Alice user linked to an initial Telegram user
    initial_telegram_user_id = 54321
    User.objects.create(
        alice_user_id="user-first-try", telegram_user_id=str(initial_telegram_user_id)
    )

    # 2. Generate a new token for a DIFFERENT Telegram user
    new_telegram_user_id = 98765
    token_words = ["четыре", "пять", "шесть"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=new_telegram_user_id,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    # 3. Simulate Alice webhook with the existing Alice user_id and the new token
    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт четыре пять шесть",
        user_id="user-first-try",
    )

    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]

    # 4. Assert that the Alice user's telegram_user_id has been updated
    user = User.objects.get(alice_user_id="user-first-try")
    assert user.telegram_user_id == str(new_telegram_user_id)
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True


def test_link_account_handler_conflict_telegram_user_id(
    client, db, secret, create_token_hash, alice_webhook_payload
):
    """
    Test: If a telegram_user_id is already linked to a different alice_user_id,
    and a new alice_user_id tries to link to that same telegram_user_id,
    the previous link should be broken and the new link established.
    """
    # 1. Create an existing User with a telegram_user_id linked to an initial alice_user_id
    existing_alice_user_id = "alice-user-old"
    telegram_id_in_conflict = 112233
    User.objects.create(
        alice_user_id=existing_alice_user_id,
        telegram_user_id=str(telegram_id_in_conflict),
    )

    # 2. Generate a token for the SAME telegram_user_id
    token_words = ["семь", "восемь", "девять"]
    token_norm = " ".join(sorted(token_words))
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=telegram_id_in_conflict,
        expires_at=timezone.now() + timedelta(days=1),
        used=False,
        token_word_count=len(token_words),
    )

    # 3. Simulate Alice webhook with a DIFFERENT alice_user_id and the token
    new_alice_user_id = "alice-user-new"
    payload = alice_webhook_payload(
        nlu_tokens=["связать", "аккаунт"] + token_words,
        original_utterance="связать аккаунт семь восемь девять",
        user_id=new_alice_user_id,
    )

    response = client.post(
        "/alice_webhook/", json.dumps(payload), content_type="application/json"
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data["response"]["text"]

    # 4. Assert that the original alice_user_id's telegram_user_id is now None (unlinked)
    old_user = User.objects.get(alice_user_id=existing_alice_user_id)
    assert old_user.telegram_user_id is None

    # 5. Assert that the new alice_user_id is now linked to the telegram_user_id
    new_user = User.objects.get(alice_user_id=new_alice_user_id)
    assert new_user.telegram_user_id == str(telegram_id_in_conflict)
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True
