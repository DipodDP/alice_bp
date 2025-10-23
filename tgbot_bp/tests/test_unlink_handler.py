
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from tgbot.handlers.user import process_unlink_command
from tgbot.messages.handlers_msg import UserHandlerMessages
from infrastructure.bp_api.api import BloodPressureApi

@pytest.mark.asyncio
async def test_unlink_command_success():
    """
    Happy path: Test that a user can successfully unlink their account.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()

    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.unlink_account.return_value = {
        "status": "unlinked",
        "message": "Аккаунты успешно отвязаны."
    }

    await process_unlink_command(message_mock, bp_api_mock)

    bp_api_mock.unlink_account.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with("Аккаунты успешно отвязаны.")

@pytest.mark.asyncio
async def test_unlink_command_not_linked():
    """
    Test that the bot replies correctly if the user's account is not linked.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()

    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.unlink_account.return_value = {
        "status": "not_linked",
        "message": "Аккаунты не были связаны."
    }

    await process_unlink_command(message_mock, bp_api_mock)

    bp_api_mock.unlink_account.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with("Аккаунты не были связаны.")

@pytest.mark.asyncio
async def test_unlink_command_api_error():
    """
    Test that the bot replies with a generic error if the API call fails.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()

    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.unlink_account.return_value = None  # Simulate API error

    await process_unlink_command(message_mock, bp_api_mock)

    bp_api_mock.unlink_account.assert_called_once_with(str(message_mock.from_user.id))
    # Assuming a generic error message for API failures
    message_mock.answer.assert_called_once_with("Произошла ошибка. Попробуйте позже.")

@pytest.mark.asyncio
async def test_unlink_command_unexpected_response():
    """
    Test that the bot handles unexpected responses from the API gracefully.
    """
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()

    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.unlink_account.return_value = {"status": "error", "unexpected_field": "value"} # Missing 'message'

    await process_unlink_command(message_mock, bp_api_mock)

    bp_api_mock.unlink_account.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with("Произошла ошибка. Попробуйте позже.")
