from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import as_key_value, as_marked_list, as_section
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select
from betterlogging import logging

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
    dialog_manager.dialog_data["user_id"] = int(item_id)
    # event = dialog_manager.event
    # middleware_data = dialog_manager.middleware_data
    # start_data = dialog_manager.start_data
    logger.debug(f"Dialog data: {dialog_manager.dialog_data}")
    await dialog_manager.switch_to(MainMenu.main)
    # or
    # await dialog_manager.next()


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
