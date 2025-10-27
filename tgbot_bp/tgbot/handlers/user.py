from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from tgbot.messages.handlers_msg import UserHandlerMessages
from tgbot.dialogs.states import MainMenu
from infrastructure.bp_api.api import BloodPressureApi


user_router = Router()


@user_router.message(Command("unlink"))
async def process_unlink_command(message: Message, bp_api: BloodPressureApi):
    """
    Handler for the /unlink command. Unlinks the user's account.
    """
    if not message.from_user:
        await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        return

    telegram_user_id = str(message.from_user.id)
    response = await bp_api.unlink_account(telegram_user_id)

    if response and response.get("message"):
        await message.answer(response.get("message"))
    else:
        await message.answer(UserHandlerMessages.UNLINK_ERROR)

    await message.delete()


@user_router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    """
    Handler for the /start command. Sends a greeting and starts the main dialog.
    """
    if not message.from_user:
        await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        return

    bp_api: BloodPressureApi = dialog_manager.middleware_data["bp_api"]
    telegram_user_id = str(message.from_user.id)
    user_data = await bp_api.get_user_by_telegram_id(telegram_user_id)

    if user_data and user_data.get("alice_user_id"):
        await message.answer(UserHandlerMessages.START_GREETING_LINKED)
        await dialog_manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
    else:
        await message.answer(UserHandlerMessages.START_GREETING)

    await message.delete()


@user_router.message(Command("link"))
async def process_link_command(message: Message, bp_api: BloodPressureApi):
    """
    Handler for the /link command. Initiates linking.
    """
    if not message.from_user:
        await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        return

    telegram_chat_id = str(message.from_user.id)

    # User sent /link (initiate linking)
    response = await bp_api.initiate_link(telegram_chat_id)
    if response and response.get("status") == "success":
        token = response.get("token")
        if token:
            await message.answer(
                UserHandlerMessages.LINK_INITIATE_SUCCESS.format(token=token)
            )
        else:
            await message.answer(UserHandlerMessages.LINK_INITIATE_ERROR)
    elif response and response.get("message"):
        await message.answer(response.get("message"))
    else:
        await message.answer(UserHandlerMessages.LINK_INITIATE_ERROR)

    await message.delete()


@user_router.message(Command("help"))
async def help_command(message: Message):
    """
    Handler for the /help command.
    """
    await message.reply(UserHandlerMessages.HELP)

    await message.delete()
