import logging

from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.exceptions import UnknownIntent

from tgbot.dialogs.states import MainMenu
from tgbot.messages.handlers_msg import UserHandlerMessages

logger = logging.getLogger(__name__)
error_router = Router()


@error_router.errors(ExceptionTypeFilter(UnknownIntent))
async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    """
    The handler for the case when the user interacts with an outdated keyboard.
    """
    logger.warning(f"User have got an UnknownIntent error: {event.exception}")

    if event.update.callback_query:
        await event.update.callback_query.answer(
            UserHandlerMessages.SESSION_EXPIRED,
        )
        await event.update.callback_query.message.delete()

    await dialog_manager.start(
        MainMenu.main,
        mode=StartMode.RESET_STACK,
    )
