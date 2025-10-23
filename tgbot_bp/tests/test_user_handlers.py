import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message
from aiogram.filters import CommandObject

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
    bp_api_mock.get_user_by_telegram_id.return_value = {"alice_user_id": "some_alice_id"}
    dialog_manager_mock.middleware_data = {"bp_api": bp_api_mock}

    await user_start(message_mock, dialog_manager_mock)

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with(UserHandlerMessages.START_GREETING_LINKED)
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

    bp_api_mock.get_user_by_telegram_id.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with(UserHandlerMessages.START_GREETING)
    dialog_manager_mock.start.assert_not_called()
    message_mock.delete.assert_called_once()


@pytest.mark.asyncio
async def test_link_command_initiate_success():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = None
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.initiate_link.return_value = {
        "status": "success",
        "code": "test-code-123",
        "message": "Ваш код для связывания: test-code-123. ..."
    }

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.initiate_link.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once()
    assert "Ваш код для связывания: test-code-123." in message_mock.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_link_command_initiate_failure():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = None
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.initiate_link.return_value = {
        "status": "error",
        "message": "Произошла ошибка при запросе кода."
    }

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.initiate_link.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with("Произошла ошибка при запросе кода.")

@pytest.mark.asyncio
async def test_link_command_complete_success():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "test-token-456"
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.complete_link.return_value = {
        "status": "success",
        "message": "Аккаунты успешно связаны!"
    }

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.complete_link.assert_called_once_with(str(message_mock.from_user.id), "test-token-456")
    message_mock.answer.assert_called_once_with("Аккаунты успешно связаны!")

@pytest.mark.asyncio
async def test_link_command_complete_failure():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "test-token-456"
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.complete_link.return_value = {
        "status": "error",
        "message": "Неверный код или срок его действия истек."
    }

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.complete_link.assert_called_once_with(str(message_mock.from_user.id), "test-token-456")
    message_mock.answer.assert_called_once_with("Неверный код или срок его действия истек.")

@pytest.mark.asyncio
async def test_link_command_initiate_api_error():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = None
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.initiate_link.return_value = None # Simulate API returning None on error

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.initiate_link.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with(UserHandlerMessages.LINK_INITIATE_ERROR)

@pytest.mark.asyncio
async def test_link_command_complete_api_error():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "test-token-456"
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.complete_link.return_value = None # Simulate API returning None on error

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.complete_link.assert_called_once_with(str(message_mock.from_user.id), "test-token-456")
    message_mock.answer.assert_called_once_with(UserHandlerMessages.LINK_ERROR)

@pytest.mark.asyncio
async def test_link_command_initiate_api_unexpected_response():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = None
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.initiate_link.return_value = {"status": "success", "unexpected_field": "value"} # Missing 'code' and 'message'

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.initiate_link.assert_called_once_with(str(message_mock.from_user.id))
    message_mock.answer.assert_called_once_with(UserHandlerMessages.LINK_INITIATE_ERROR)

@pytest.mark.asyncio
async def test_link_command_complete_api_unexpected_response():
    message_mock = AsyncMock(spec=Message)
    message_mock.from_user = MagicMock()
    message_mock.from_user.id = 12345
    message_mock.answer = AsyncMock()
    command_mock = MagicMock(spec=CommandObject)
    command_mock.args = "test-token-456"
    bp_api_mock = AsyncMock(spec=BloodPressureApi)
    bp_api_mock.complete_link.return_value = {"status": "success", "unexpected_field": "value"} # Missing 'message'

    await process_link_command(message_mock, command_mock, bp_api_mock)

    bp_api_mock.complete_link.assert_called_once_with(str(message_mock.from_user.id), "test-token-456")
    message_mock.answer.assert_called_once_with(UserHandlerMessages.LINK_SUCCESS)
