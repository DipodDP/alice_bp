from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Update
from aiogram.types.error_event import ErrorEvent
from aiogram_dialog import DialogManager, StartMode

from tgbot.dialogs.states import MainMenu
from tgbot.handlers.error import on_unknown_intent
from tgbot.messages.handlers_msg import UserHandlerMessages


@pytest.fixture
def mock_error_event_with_callback_query():
    callback_query = MagicMock(spec=CallbackQuery)
    callback_query.answer = AsyncMock()
    callback_query.message = AsyncMock()
    callback_query.message.delete = AsyncMock()
    update = MagicMock(spec=Update)
    update.callback_query = callback_query
    error_event = MagicMock(spec=ErrorEvent)
    error_event.update = update
    error_event.exception = MagicMock()
    return error_event


@pytest.fixture
def mock_dialog_manager():
    dialog_manager = AsyncMock(spec=DialogManager)
    dialog_manager.start = AsyncMock()
    return dialog_manager


@pytest.mark.asyncio
async def test_on_unknown_intent(
    mock_error_event_with_callback_query, mock_dialog_manager
):
    await on_unknown_intent(mock_error_event_with_callback_query, mock_dialog_manager)

    mock_error_event_with_callback_query.update.callback_query.answer.assert_called_once_with(
        UserHandlerMessages.SESSION_EXPIRED,
    )
    mock_error_event_with_callback_query.update.callback_query.message.delete.assert_called_once()
    mock_dialog_manager.start.assert_called_once_with(
        MainMenu.main,
        mode=StartMode.RESET_STACK,
    )
