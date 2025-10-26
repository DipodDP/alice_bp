import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message

from tgbot.handlers.user import process_link_command, user_start
from tgbot.messages.handlers_msg import UserHandlerMessages
from infrastructure.bp_api.api import BloodPressureApi
from aiogram_dialog import DialogManager


@pytest.mark.asyncio
async def test_user_start_linked():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    message_mock.delete = AsyncMock()
    dialog_manager_mock = AsyncMock(spec=DialogManager)
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "alice_user_id": "some_alice_id"
    }
    dialog_manager_mock.middleware_data = {"bp_api": bp_api_mock}

    await user_start(message_mock, dialog_manager_mock)

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(
        str(message_mock.from_user.id)
    )
    message_mock.answer.assert_called_once_with(
        UserHandlerMessages.START_GREETING_LINKED
    )
    dialog_manager_mock.start.assert_called_once()
    message_mock.delete.assert_called_once()


@pytest.mark.asyncio
async def test_user_start_not_linked():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    message_mock.delete = AsyncMock()
    dialog_manager_mock = AsyncMock(spec=DialogManager)
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.get_user_by_telegram_id.return_value = None
    dialog_manager_mock.middleware_data = {"bp_api": bp_api_mock}

    await user_start(message_mock, dialog_manager_mock)

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(
        str(message_mock.from_user.id)
    )
    message_mock.answer.assert_called_once_with(UserHandlerMessages.START_GREETING)
    dialog_manager_mock.start.assert_not_called()
    message_mock.delete.assert_called_once()


@pytest.mark.parametrize(
    "api_return_value, expected_message_type, expected_token",
    [
        (
            {"status": "success", "token": "мост-627"},
            "success_with_token",
            "мост-627",
        ),
        (
            {"status": "error", "message": "Произошла ошибка при запросе кода."},
            "api_message",
            None,
        ),
        (None, "default_error", None),
        ({"status": "success", "unexpected_field": "value"}, "default_error", None),
    ],
)
@pytest.mark.asyncio
async def test_process_link_command_parameterized(
    message_mock, bp_api_mock, api_return_value, expected_message_type, expected_token
):
    """
    Test process_link_command with various API responses using parametrization.
    """
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()

    bp_api_mock.initiate_link.return_value = api_return_value

    await process_link_command(message_mock, bp_api_mock)

    bp_api_mock.initiate_link.assert_called_once_with(str(message_mock.from_user.id))

    if expected_message_type == "success_with_token":
        expected_message = UserHandlerMessages.LINK_INITIATE_SUCCESS.format(
            token=expected_token
        )
    elif expected_message_type == "api_message":
        expected_message = api_return_value.get("message")
    else:  # default_error
        expected_message = UserHandlerMessages.LINK_INITIATE_ERROR

    message_mock.answer.assert_called_once_with(expected_message)
