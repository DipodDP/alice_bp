import logging
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select

from tgbot.keyboards.reply import user_menu_keyboard
from tgbot.messages.handlers_msg import UserHandlerMessages
from tgbot.dialogs.states import MainMenu

logger = logging.getLogger(__name__)


async def set_prev_message(
    callback_query: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
):
    if not isinstance(callback_query.message, Message):
        return
    data = dialog_manager.middleware_data
    state: FSMContext = data["state"]
    await callback_query.message.delete()
    answer = await callback_query.message.answer(
        UserHandlerMessages.CANCEL, reply_markup=user_menu_keyboard()
    )
    await state.update_data(prev_bot_message=answer)


async def selected_interval(
    callback_query: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    """Handle interval selection and store the selected interval."""
    selected_interval = int(item_id)
    dialog_manager.dialog_data["selected_interval"] = selected_interval

    logger.info(f"Selected interval: {selected_interval}")

    # Switch to the results window to show pressure data
    await dialog_manager.switch_to(MainMenu.pressure_results)


async def selected_measurement(
    callback_query: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str,
):
    """Get pressure measurement options."""
    logger.error("Options are not implemented for now")


async def action_done(
    callback_query: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
):
    if not isinstance(callback_query.message, Message):
        return
    data = dialog_manager.middleware_data
    state: FSMContext = data["state"]
    await callback_query.message.delete()
    answer = await callback_query.message.answer(
        UserHandlerMessages.COMPLETED, reply_markup=user_menu_keyboard()
    )
    await state.update_data(prev_bot_message=answer)
    await dialog_manager.done()
