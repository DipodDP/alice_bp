import pytest
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from alice_skill.models import AccountLinkToken

# Mock settings for testing
@pytest.fixture(autouse=True)
def setup_django_settings():
    settings.configure(
        SECRET_KEY='test-secret-key',
        DEBUG=True,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'alice_skill',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        LINK_SECRET="test-secret"
    )
    # Initialize Django apps
    import django
    django.setup()

@pytest.fixture
def client():
    from django.test import Client
    return Client()

@pytest.fixture
def db(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Ensure the database is clean for each test
        AccountLinkToken.objects.all().delete()
        yield
        AccountLinkToken.objects.all().delete()

@pytest.fixture
def secret():
    return "test-secret"

@pytest.fixture
def create_token_hash(secret):
    def _create_token_hash(token_norm):
        return hmac.new(secret.encode('utf-8'), token_norm.encode('utf-8'), hashlib.sha256).hexdigest()
    return _create_token_hash

@pytest.fixture
def alice_webhook_payload(session_id="test-session", message_id=1, user_id="test-user"):
    def _payload(nlu_tokens=None, original_utterance="", command=""):
        payload = {
            "meta": {
                "locale": "ru-RU",
                "timezone": "Europe/Moscow",
                "client_id": "ru.yandex.searchplugin/7.16 (lge Nexus 5X; Android 8.1.0)",
                "interfaces": {
                    "screen": {},
                    "payments": {},
                    "account_linking": {}
                }
            },
            "session": {
                "message_id": message_id,
                "session_id": session_id,
                "skill_id": "test-skill-id",
                "user_id": user_id,
                "new": False
            },
            "request": {
                "command": command,
                "original_utterance": original_utterance,
                "type": "SimpleUtterance",
                "nlu": {
                    "tokens": nlu_tokens if nlu_tokens is not None else [],
                    "entities": []
                }
            },
            "version": "1.0"
        }
        return payload
    return _payload

# Iteration 0 - Smoke Tests (failing)

def test_smoke_valid_token_nlu_tokens_fails(client, db, create_token_hash, alice_webhook_payload):
    """
    Test A: Send payload with valid token in nlu.tokens.
    Expects successful linking, but current handler should fail.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    payload = alice_webhook_payload(nlu_tokens=["мост", "белый", "дом"], original_utterance="мост белый дом")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Не удалось распознать цифры давления или команду" not in response_data["response"]["text"]
    assert "Аккаунты связаны" in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_smoke_invalid_token_nlu_tokens_fails(client, db, create_token_hash, alice_webhook_payload):
    """
    Test B: Send payload with invalid token in nlu.tokens (not in DB).
    Expects failure (original error message).
    """
    payload = alice_webhook_payload(nlu_tokens=["не", "существующий", "токен"], original_utterance="не существующий токен")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Не удалось распознать цифры давления или команду" in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert not AccountLinkToken.objects.filter(token_hash=create_token_hash("не существующий токен")).exists()

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
    assert normalize_spoken_token_func(["  мост  ", "  белый  ", "  дом  "]) == "мост белый дом"

def test_normalize_spoken_token_yo_to_e(normalize_spoken_token_func):
    assert normalize_spoken_token_func(["ёлка", "мёд", "пёс"]) == "елка мед пес"

def test_iteration2_nlu_tokens_primary_extraction(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: when nlu.tokens = ["мост","белый","дом"], handler calls normalize_spoken_token,
    computes token_hash = HMAC(SECRET, token_norm), and finds the matching token row in DB.
    Expected: Alice JSON with "text":"Аккаунты связаны. Спасибо!", HTTP 200, and DB: link_tokens.used == true.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    payload = alice_webhook_payload(nlu_tokens=["мост", "белый", "дом"], original_utterance="мост белый дом")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_iteration3_nlu_tokens_fragmented(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: nlu.tokens might be ["мост","бел","ый","дом"] or include noise tokens;
    implement logic to find the best consecutive sequence of three valid Russian-word tokens.
    Expect success when three-word sequence present.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    # Case 1: Fragmented tokens
    payload = alice_webhook_payload(nlu_tokens=["какой-то", "шум", "мост", "белый", "дом", "еще", "слова"], original_utterance="какой-то шум мост белый дом еще слова")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Аккаунты связаны. Спасибо!" in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

    # Reset token for next test case
    AccountLinkToken.objects.filter(token_hash=token_hash).update(used=False)

    # Case 2: Fragmented with partial words (should still normalize)
    payload = alice_webhook_payload(nlu_tokens=["начало", "мост", "бел", "ый", "дом", "конец"], original_utterance="начало мост бел ый дом конец")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Аккаунты связаны. Спасибо!" in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_iteration3_nlu_tokens_no_valid_triple(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: nlu.tokens does not contain a valid three-word sequence.
    Expects failure (original error message).
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    payload = alice_webhook_payload(nlu_tokens=["один", "два", "четыре"], original_utterance="один два четыре")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Не удалось распознать цифры давления или команду" in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_iteration5_advanced_asr_morphological_variants(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: nlu.tokens contains morphological variants, but normalization should still match.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    # Morphological variants (e.g., different endings)
    payload = alice_webhook_payload(nlu_tokens=["моста", "белого", "дома"], original_utterance="моста белого дома")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Аккаунты связаны. Спасибо!" in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_iteration5_advanced_asr_extra_words_and_punctuation(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: nlu.tokens contains extra words and punctuation, but the core triple should be recovered.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    # Extra words and punctuation
    payload = alice_webhook_payload(nlu_tokens=["пожалуйста", "скажи", "мост,", "белый", "дом!", "спасибо"], original_utterance="пожалуйста скажи мост, белый дом! спасибо")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Аккаунты связаны. Спасибо!" in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True

def test_iteration5_advanced_asr_no_match_after_normalization(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: nlu.tokens contains words that, even after normalization, do not form a valid triple.
    Expects failure.
    """
    token_norm = "мост белый дом"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=12345,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    payload = alice_webhook_payload(nlu_tokens=["один", "два", "четыре", "пять"], original_utterance="один два четыре пять")
    response = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data = response.json()

    assert response.status_code == 200
    assert "Не удалось распознать цифры давления или команду" in response_data["response"]["text"]
    assert "Аккаунты связаны" not in response_data["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is False

def test_iteration4_token_one_time_use(client, db, secret, create_token_hash, alice_webhook_payload):
    """
    Test: Attempt to reuse the same token twice.
    First call: success. Second call: failure with message "token already used".
    """
    token_norm = "один два три"
    token_hash = create_token_hash(token_norm)
    AccountLinkToken.objects.create(
        token_hash=token_hash,
        telegram_user_id=None,
        expires_at=timezone.now() + timedelta(days=1),
        used=False
    )

    payload = alice_webhook_payload(nlu_tokens=["один", "два", "три"], original_utterance="один два три", user_id="user-first-try")

    # First attempt: should succeed
    response1 = client.post('/alice_skill/webhook/', json.dumps(payload), content_type='application/json')
    response_data1 = response1.json()

    assert response1.status_code == 200
    assert "Аккаунты связаны. Спасибо!" in response_data1["response"]["text"]
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True
    assert AccountLinkToken.objects.get(token_hash=token_hash).telegram_user_id == "user-first-try"

    # Second attempt with the same token: should fail
    payload_second = alice_webhook_payload(nlu_tokens=["один", "два", "три"], original_utterance="один два три", user_id="user-second-try")
    response2 = client.post('/alice_skill/webhook/', json.dumps(payload_second), content_type='application/json')
    response_data2 = response2.json()

    assert response2.status_code == 200
    assert "Не удалось распознать цифры давления или команду" in response_data2["response"]["text"]
    assert "Аккаунты связаны" not in response_data2["response"]["text"]
    # Ensure the token remains used=True and linked to the first user
    assert AccountLinkToken.objects.get(token_hash=token_hash).used is True
    assert AccountLinkToken.objects.get(token_hash=token_hash).telegram_user_id == "user-first-try"

