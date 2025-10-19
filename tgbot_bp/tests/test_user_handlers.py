import pytest
from unittest.mock import AsyncMock, MagicMock

from tgbot.handlers.user import process_link_command
from tgbot.messages.handlers_msg import UserHandlerMessages

# Маркируем все тесты в этом файле как асинхронные
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_message():
    """Фикстура для создания мока сообщения от пользователя."""
    message = MagicMock()
    message.answer = AsyncMock()
    message.from_user = MagicMock()
    message.from_user.id = 12345678
    return message


@pytest.fixture
def mock_bp_api():
    """Фикстура для создания мока API клиента."""
    api = MagicMock()
    api.complete_link = AsyncMock()
    return api


@pytest.fixture
def mock_command():
    """Фикстура для создания мока объекта команды."""
    command = MagicMock()
    command.args = None
    return command


async def test_process_link_command_no_token(mock_message, mock_command, mock_bp_api):
    """Тест: пользователь отправил /link без кода."""
    # Arrange
    mock_command.args = ""

    # Act
    await process_link_command(mock_message, mock_command, mock_bp_api)

    # Assert
    mock_message.answer.assert_called_once_with(UserHandlerMessages.LINK_NO_CODE)
    mock_bp_api.complete_link.assert_not_called()


async def test_process_link_command_success(mock_message, mock_command, mock_bp_api):
    """Тест: пользователь отправил /link с верным кодом."""
    # Arrange
    token = "VALID-CODE"
    mock_command.args = token
    mock_bp_api.complete_link.return_value = {
        "status": "success",
        "message": "Аккаунты успешно связаны!"
    }

    # Act
    await process_link_command(mock_message, mock_command, mock_bp_api)

    # Assert
    mock_bp_api.complete_link.assert_called_once_with(mock_message.from_user.id, token)
    mock_message.answer.assert_called_once_with("Аккаунты успешно связаны!")


async def test_process_link_command_api_error(mock_message, mock_command, mock_bp_api):
    """Тест: API вернуло ошибку (например, неверный код)."""
    # Arrange
    token = "INVALID-CODE"
    mock_command.args = token
    mock_bp_api.complete_link.return_value = {
        "status": "error",
        "message": "Неверный код или срок его действия истек."
    }

    # Act
    await process_link_command(mock_message, mock_command, mock_bp_api)

    # Assert
    mock_bp_api.complete_link.assert_called_once_with(mock_message.from_user.id, token)
    mock_message.answer.assert_called_once_with("Неверный код или срок его действия истек.")


async def test_process_link_command_api_exception(mock_message, mock_command, mock_bp_api):
    """Тест: при вызове API произошло исключение."""
    # Arrange
    token = "VALID-CODE"
    mock_command.args = token
    mock_bp_api.complete_link.return_value = None  # API клиент возвращает None при ClientError

    # Act
    await process_link_command(mock_message, mock_command, mock_bp_api)

    # Assert
    mock_bp_api.complete_link.assert_called_once_with(mock_message.from_user.id, token)
    mock_message.answer.assert_called_once_with(UserHandlerMessages.LINK_ERROR)