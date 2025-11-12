import logging

from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent
from aiogram.fsm.context import FSMContext
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.exceptions import UnknownIntent
from aiogram_dialog.api.entities.modes import ShowMode

from tgbot.dialogs.states import MainMenu
from tgbot.messages.handlers_msg import UserHandlerMessages

logger = logging.getLogger(__name__)
error_router = Router()


@error_router.errors(ExceptionTypeFilter(UnknownIntent))
async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    """
    The handler for the case when the user interacts with an outdated keyboard.
    """
    logger.warning(f'User have got an UnknownIntent error: {event.exception}')

    message_to_edit = None
    if event.update.callback_query:
        await event.update.callback_query.answer(
            UserHandlerMessages.SESSION_EXPIRED,
        )
        message_to_edit = event.update.callback_query.message

    # If we have a message to edit, tell the dialog manager to edit it
    if message_to_edit:
        # Store the message in state so dialog knows which message to edit
        state: FSMContext = dialog_manager.middleware_data['state']
        await state.update_data(keyboard_message=message_to_edit)
        # Set show mode to EDIT so dialog edits the existing message
        dialog_manager.show_mode = ShowMode.EDIT

    # Start the dialog - it will edit the existing message if show_mode is EDIT
    await dialog_manager.start(
        MainMenu.main,
        mode=StartMode.RESET_STACK,
    )
