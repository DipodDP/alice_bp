from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.exceptions import TelegramAPIError
from betterlogging import logging


logger = logging.getLogger(__name__)


async def delete_prev_message(state: FSMContext):
    state_data = await state.get_data()

    state_data = await state.get_data()

    prev_bot_message: Message | None = state_data.get("prev_bot_message")
    if prev_bot_message is not None:
        try:
            await prev_bot_message.delete()
        except TelegramAPIError as e:
            logger.warning(
                "Failed to delete previous bot message (ID: %s, Chat ID: %s): %s",
                prev_bot_message.message_id,
                prev_bot_message.chat.id,
                e.message,
                exc_info=False,
            )
    else:
        logger.debug("No prev_bot_message found in state to delete.")

    keyboard_message: Message | None = state_data.get("keyboard_message")
    if keyboard_message is not None:
        try:
            await keyboard_message.delete()
        except TelegramAPIError as e:
            logger.warning(
                "Failed to delete keyboard message (ID: %s, Chat ID: %s): %s",
                keyboard_message.message_id,
                keyboard_message.chat.id,
                e.message,
                exc_info=False,
            )
    else:
        logger.debug("No keyboard_message found in state to delete.")
