import json
import hmac
import hashlib
import secrets
from datetime import timedelta

import pytest
from django.utils import timezone

from ...messages import LinkAccountMessages, HandlerMessages
from ...models import AccountLinkToken, AliceUser
from ...wordlist import WORDLIST
from ...helpers import get_hashed_telegram_id


@pytest.fixture(autouse=True)
def alice_secret(settings):
    settings.ALICE_WEBHOOK_SECRET = 'test-secret'


# Mock settings for testing


@pytest.fixture
def secret():
    return 'a-super-secret-key'


@pytest.fixture
def create_token_hash(secret):
    def _create_token_hash(token_norm):
        return hmac.new(
            secret.encode('utf-8'), token_norm.encode('utf-8'), hashlib.sha256
        ).hexdigest()

    return _create_token_hash


@pytest.fixture
def create_word_number_token(secret):
    def _create_word_number_token(telegram_user_id, expires_in_minutes=10, used=False):
        random_word = secrets.SystemRandom().choice(WORDLIST)
        random_number = secrets.SystemRandom().randint(100, 999)
        plaintext_token = f'{random_word}-{random_number}'
        normalized_token = plaintext_token.lower()
        token_hash = hmac.new(
            secret.encode(), normalized_token.encode(), 'sha256'
        ).hexdigest()
        expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)

        # Ensure the ID is hashed before storing, mimicking the real application flow
        hashed_telegram_id = get_hashed_telegram_id(telegram_user_id)

        account_link_token = AccountLinkToken.objects.create(
            token_hash=token_hash,
            telegram_user_id_hash=hashed_telegram_id,
            expires_at=expires_at,
            used=used,
        )
        return plaintext_token, account_link_token

    return _create_word_number_token


@pytest.fixture
def alice_webhook_payload(session_id='test-session', message_id=1, user_id='test-user'):
    def _payload(nlu_tokens=None, original_utterance='', command='', user_id=user_id):
        payload = {
            'meta': {
                'locale': 'ru-RU',
                'timezone': 'Europe/Moscow',
                'client_id': 'ru.yandex.searchplugin/7.16 (lge Nexus 5X; Android 8.1.0)',
                'interfaces': {'screen': {}, 'payments': {}, 'account_linking': {}},
            },
            'session': {
                'message_id': message_id,
                'session_id': session_id,
                'skill_id': 'test-skill-id',
                'user_id': user_id,
                'new': False,
            },
            'request': {
                'command': command,
                'original_utterance': original_utterance,
                'type': 'SimpleUtterance',
                'nlu': {
                    'tokens': nlu_tokens if nlu_tokens is not None else [],
                    'entities': [],
                },
            },
            'version': '1.0',
        }
        return payload

    return _payload


# New tests for word-number token linking


def test_link_account_handler_with_word_number_code_success(
    client, db, create_word_number_token, alice_webhook_payload
):
    telegram_user_id = '12345'
    plaintext_token, account_link_token = create_word_number_token(
        telegram_user_id=telegram_user_id
    )

    payload = alice_webhook_payload(
        original_utterance=f'связать аккаунт {plaintext_token}',
        nlu_tokens=f'связать аккаунт {plaintext_token}'.split(),
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data['response']['text']
    assert AccountLinkToken.objects.get(pk=account_link_token.pk).used is True
    assert AliceUser.objects.get(
        alice_user_id='test-alice-user-id'
    ).telegram_user_id_hash == get_hashed_telegram_id(telegram_user_id)


def test_link_account_handler_with_word_number_code_fail_invalid_code(
    client, db, alice_webhook_payload
):
    """
    Test: Failed linking when utterance contains an invalid word-number code (not in DB).
    """
    invalid_token = 'неслово-000'
    payload = alice_webhook_payload(
        original_utterance=f'связать аккаунт {invalid_token}',
        nlu_tokens=f'связать аккаунт {invalid_token}'.split(),
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.FAIL in response_data['response']['text']
    assert 'Аккаунты связаны' not in response_data['response']['text']


def test_link_account_handler_with_word_number_code_fail_expired_code(
    client, db, create_word_number_token, alice_webhook_payload
):
    """
    Test: Failed linking when utterance contains an expired word-number code.
    """
    plaintext_token, account_link_token = create_word_number_token(
        telegram_user_id='12345', expires_in_minutes=-10
    )

    payload = alice_webhook_payload(
        original_utterance=f'связать аккаунт {plaintext_token}',
        nlu_tokens=f'связать аккаунт {plaintext_token}'.split(),
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.FAIL in response_data['response']['text']
    assert 'Аккаунты связаны' not in response_data['response']['text']
    assert AccountLinkToken.objects.get(pk=account_link_token.pk).used is False


def test_link_account_handler_instructions_no_code(client, db, alice_webhook_payload):
    """
    Test: When utterance contains a trigger but no word-number code, provide instructions.
    """
    payload = alice_webhook_payload(
        original_utterance='связать аккаунт',
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert (
        LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS
        in response_data['response']['text']
    )


def test_link_account_handler_instructions_no_code_with_other_words(
    client, db, alice_webhook_payload
):
    """
    Test: When utterance contains a trigger and other words but no word-number code, provide instructions.
    """
    payload = alice_webhook_payload(
        original_utterance='привяжи телеграм пожалуйста',
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert (
        LinkAccountMessages.ACCOUNT_LINKING_INSTRUCTIONS
        in response_data['response']['text']
    )


def test_link_account_handler_no_trigger_no_code(client, db, alice_webhook_payload):
    """
    Test: When utterance contains neither a trigger nor a word-number code, handler should return None.
    """
    payload = alice_webhook_payload(
        original_utterance='просто какой-то текст',
        user_id='test-alice-user-id',
    )
    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert HandlerMessages.ERROR_UNPARSED in response_data['response']['text']


def test_link_account_handler_update_telegram_user_id(
    client, db, create_word_number_token, alice_webhook_payload
):
    """
    Test: If an Alice user already exists and is linked to a Telegram user,
    linking them to a new Telegram user should update the telegram_user_id_hash for that Alice user.
    """
    # 1. Create an existing Alice user linked to an initial Telegram user
    initial_telegram_user_id = '54321'
    AliceUser.objects.create(
        alice_user_id='user-first-try',
        telegram_user_id_hash=get_hashed_telegram_id(initial_telegram_user_id),
    )

    # 2. Generate a new token for a DIFFERENT Telegram user
    new_telegram_user_id = '98765'
    plaintext_token, account_link_token = create_word_number_token(
        telegram_user_id=new_telegram_user_id
    )

    # 3. Simulate Alice webhook with the existing Alice user_id and the new token
    payload = alice_webhook_payload(
        original_utterance=f'связать аккаунт {plaintext_token}',
        nlu_tokens=f'связать аккаунт {plaintext_token}'.split(),
        user_id='user-first-try',
    )

    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data['response']['text']

    # 4. Assert that the Alice user's telegram_user_id_hash has been updated
    user = AliceUser.objects.get(alice_user_id='user-first-try')
    assert user.telegram_user_id_hash == get_hashed_telegram_id(new_telegram_user_id)
    assert AccountLinkToken.objects.get(pk=account_link_token.pk).used is True


def test_link_account_handler_conflict_telegram_user_id(
    client, db, create_word_number_token, alice_webhook_payload
):
    """
    Test: If a telegram_user_id is already linked to a different alice_user_id,
    and a new alice_user_id tries to link to that same telegram_user_id,
    the previous link should be broken and the new link established.
    """
    # 1. Create an existing User with a telegram_user_id_hash linked to an initial alice_user_id
    existing_alice_user_id = 'alice-user-old'
    telegram_id_in_conflict = '112233'
    AliceUser.objects.create(
        alice_user_id=existing_alice_user_id,
        telegram_user_id_hash=get_hashed_telegram_id(telegram_id_in_conflict),
    )

    # 2. Generate a token for the SAME telegram_user_id
    plaintext_token, account_link_token = create_word_number_token(
        telegram_user_id=telegram_id_in_conflict
    )

    # 3. Simulate Alice webhook with a DIFFERENT alice_user_id and the token
    new_alice_user_id = 'alice-user-new'
    payload = alice_webhook_payload(
        original_utterance=f'связать аккаунт {plaintext_token}',
        nlu_tokens=f'связать аккаунт {plaintext_token}'.split(),
        user_id=new_alice_user_id,
    )

    response = client.post(
        '/alice_webhook/?token=test-secret',
        json.dumps(payload),
        content_type='application/json',
    )
    response_data = response.json()

    assert response.status_code == 200
    assert LinkAccountMessages.SUCCESS in response_data['response']['text']

    # 4. Assert that the original alice_user_id's telegram_user_id_hash is now None (unlinked)
    old_user = AliceUser.objects.get(alice_user_id=existing_alice_user_id)
    assert old_user.telegram_user_id_hash is None

    # 5. Assert that the new alice_user_id is now linked to the telegram_user_id_hash
    new_user = AliceUser.objects.get(alice_user_id=new_alice_user_id)
    assert new_user.telegram_user_id_hash == get_hashed_telegram_id(telegram_id_in_conflict)
    assert AccountLinkToken.objects.get(pk=account_link_token.pk).used is True
