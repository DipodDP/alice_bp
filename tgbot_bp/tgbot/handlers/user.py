from aiogram import Router
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from tgbot.messages.handlers_msg import UserHandlerMessages
from tgbot.dialogs.states import MainMenu
from infrastructure.bp_api.api import BloodPressureApi

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    """
    Handler for the /start command. Sends a greeting and starts the main dialog.
    """
    # Send an informational message about linking first
    await message.answer(UserHandlerMessages.START_GREETING)
    # Then, start the main dialog as before
    await dialog_manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
    await message.delete()


@user_router.message(Command("link"))
async def process_link_command(message: Message, command: CommandObject, bp_api: BloodPressureApi):
    """
    Handler for the /link <token> command.
    """
    token = command.args
    if not token:
        await message.answer(UserHandlerMessages.LINK_NO_CODE)
        return

    if not message.from_user:
        # This case is unlikely in private chats but good for type safety
        await message.answer("Не могу определить ваш профиль.")
        return

    response = await bp_api.complete_link(message.from_user.id, token)

    if response and response.get("status") == "success":
        await message.answer(response.get("message", UserHandlerMessages.LINK_SUCCESS))
    elif response and response.get("message"):
        # If the API returned a specific error message, show it
        await message.answer(response.get("message"))
    else:
        # Generic error if the API is unavailable or returned an unexpected response
        await message.answer(UserHandlerMessages.LINK_ERROR)


@user_router.message(Command('help'))
async def help_command(message: Message):
    """
    Handler for the /help command.
    """
    await message.reply(UserHandlerMessages.HELP)