import pytest
from unittest.mock import AsyncMock, patch
from aiogram_dialog import DialogManager

from tgbot.handlers.user import (
    help_command,
    process_link_command,
    user_start,
)
from tgbot.messages.handlers_msg import UserHandlerMessages



@pytest.mark.asyncio
@patch("tgbot.handlers.user.delete_prev_message", new_callable=AsyncMock)
async def test_user_start_linked(mock_delete_prev_message, message_mock, state_mock, bp_api_mock):
    dialog_manager_mock = AsyncMock(spec=DialogManager)
    bp_api_mock.get_user_by_telegram_id.return_value = {
        "alice_user_id": "some_alice_id"
    }
    dialog_manager_mock.middleware_data = {
        "bp_api": bp_api_mock,
        "state": state_mock,
    }

    await user_start(message_mock, dialog_manager_mock)

    mock_delete_prev_message.assert_called_once_with(state_mock)
    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(
        str(message_mock.from_user.id)
    )
    message_mock.answer.assert_called_once_with(
        UserHandlerMessages.START_GREETING_LINKED
    )
    state_mock.update_data.assert_called_once()
    dialog_manager_mock.start.assert_called_once()
    message_mock.delete.assert_called_once()


@pytest.mark.asyncio
@patch("tgbot.handlers.user.delete_prev_message", new_callable=AsyncMock)
async def test_user_start_not_linked(mock_delete_prev_message, message_mock, state_mock, bp_api_mock):
    dialog_manager_mock = AsyncMock(spec=DialogManager)
    bp_api_mock.get_user_by_telegram_id.return_value = None
    dialog_manager_mock.middleware_data = {
        "bp_api": bp_api_mock,
        "state": state_mock,
    }

    await user_start(message_mock, dialog_manager_mock)

    mock_delete_prev_message.assert_called_once_with(state_mock)
    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(
        str(message_mock.from_user.id)
    )
    message_mock.answer.assert_called_once_with(UserHandlerMessages.START_GREETING)
    state_mock.update_data.assert_called_once()
    dialog_manager_mock.start.assert_not_called()
    message_mock.delete.assert_called_once()


@pytest.mark.parametrize(
    "api_return_value, expected_message_type, expected_token",
    [
        (
            {"status": "success", "token": "bridge-627"},
            "success_with_token",
            "bridge-627",
        ),
        (
            {"status": "error", "message": "Error requesting code."},
            "api_message",
            None,
        ),
        (None, "default_error", None),
        ({"status": "success", "unexpected_field": "value"}, "default_error", None),
    ],
)
@pytest.mark.asyncio
@patch("tgbot.handlers.user.delete_prev_message", new_callable=AsyncMock)
async def test_process_link_command_parameterized(
    mock_delete_prev_message,
    message_mock,
    bp_api_mock,
    state_mock,
    api_return_value,
    expected_message_type,
    expected_token,
):
    """
    Test process_link_command with various API responses using parametrization.
    """
    bp_api_mock.initiate_link.return_value = api_return_value

    await process_link_command(message_mock, bp_api_mock, state_mock)

    mock_delete_prev_message.assert_called_once_with(state_mock)
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
    state_mock.update_data.assert_called_once()



@pytest.mark.asyncio
@patch("tgbot.handlers.user.delete_prev_message", new_callable=AsyncMock)
async def test_help_command(mock_delete_prev_message, message_mock, state_mock):
    await help_command(message_mock, state_mock)

    mock_delete_prev_message.assert_called_once_with(state_mock)
    message_mock.answer.assert_called_once_with(UserHandlerMessages.HELP)
    state_mock.update_data.assert_called_once()
