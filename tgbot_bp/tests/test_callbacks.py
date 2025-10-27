import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.fsm.context import FSMContext

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from tgbot.dialogs.callbacks import action_done, set_prev_message


@pytest.fixture
def mock_callback_query():
    cq = AsyncMock(spec=CallbackQuery)
    cq.message = AsyncMock(spec=Message)
    cq.message.delete = AsyncMock()
    cq.message.answer = AsyncMock()
    return cq


@pytest.fixture
def mock_dialog_manager():
    dm = AsyncMock(spec=DialogManager)
    dm.middleware_data = {"state": AsyncMock(spec=FSMContext)}
    return dm


@pytest.fixture
def mock_button():
    return MagicMock(spec=Button)


@pytest.mark.asyncio
@patch("tgbot.dialogs.callbacks.delete_prev_message", new_callable=AsyncMock)
async def test_set_prev_message_deletes_previous(
    mock_delete_prev_message, mock_callback_query, mock_button, mock_dialog_manager
):
    state_mock = mock_dialog_manager.middleware_data["state"]

    await set_prev_message(mock_callback_query, mock_button, mock_dialog_manager)

    mock_delete_prev_message.assert_called_once_with(state_mock)
    state_mock.update_data.assert_called_once_with(prev_bot_message=mock_callback_query.message)
    mock_callback_query.message.delete.assert_not_called()
    mock_callback_query.message.answer.assert_not_called()


@pytest.mark.asyncio
@patch("tgbot.dialogs.callbacks.delete_prev_message", new_callable=AsyncMock)
async def test_action_done_deletes_previous(
    mock_delete_prev_message, mock_callback_query, mock_button, mock_dialog_manager
):
    state_mock = mock_dialog_manager.middleware_data["state"]

    await action_done(mock_callback_query, mock_button, mock_dialog_manager)

    mock_delete_prev_message.assert_called_once_with(state_mock)
    mock_callback_query.message.delete.assert_called_once()
    mock_callback_query.message.answer.assert_called_once()
    state_mock.update_data.assert_called_once()
    mock_dialog_manager.done.assert_called_once()
