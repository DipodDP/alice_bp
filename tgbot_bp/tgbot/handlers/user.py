from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from tgbot.messages.handlers_msg import UserHandlerMessages
from tgbot.dialogs.states import MainMenu

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
    await message.delete()


@user_router.message(Command('help'))
async def help(message: Message):
    await message.reply(UserHandlerMessages.HELP)
