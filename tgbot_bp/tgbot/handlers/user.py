from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode

from infrastructure.bp_api.api import BloodPressureApi
from tgbot.dialogs.states import MainMenu
from tgbot.messages.handlers_msg import UserHandlerMessages
from tgbot.services.utils import delete_prev_message


user_router = Router()


@user_router.message(Command("unlink"))
async def process_unlink_command(
    message: Message, bp_api: BloodPressureApi, state: FSMContext
):
    """
    Handler for the /unlink command. Unlinks the user's account.
    """
    await message.delete()
    await delete_prev_message(state)

    if not message.from_user:
        answer = await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        await state.update_data(prev_bot_message=answer)
        return

    telegram_user_id = str(message.from_user.id)
    response = await bp_api.unlink_account(telegram_user_id)

    if response and response.get("message"):
        answer = await message.answer(response.get("message"))
    else:
        answer = await message.answer(UserHandlerMessages.UNLINK_ERROR)

    await state.update_data(prev_bot_message=answer)


@user_router.message(CommandStart())
async def user_start(message: Message, dialog_manager: DialogManager):
    """
    Handler for the /start command. Sends a greeting and starts the main dialog.
    """
    await message.delete()
    state: FSMContext = dialog_manager.middleware_data["state"]
    await delete_prev_message(state)

    if not message.from_user:
        answer = await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        await state.update_data(prev_bot_message=answer)
        return

    bp_api: BloodPressureApi = dialog_manager.middleware_data["bp_api"]
    telegram_user_id = str(message.from_user.id)
    user_data = await bp_api.get_user_by_telegram_id(telegram_user_id)

    if user_data and user_data.get("alice_user_id"):
        answer = await message.answer(UserHandlerMessages.START_GREETING_LINKED)
        await state.update_data(prev_bot_message=answer)
        await dialog_manager.start(MainMenu.main, mode=StartMode.RESET_STACK)
    else:
        answer = await message.answer(UserHandlerMessages.START_GREETING)
        await state.update_data(prev_bot_message=answer)


@user_router.message(Command("link"))
async def process_link_command(
    message: Message, bp_api: BloodPressureApi, state: FSMContext
):
    """
    Handler for the /link command. Initiates linking.
    """
    await message.delete()
    await delete_prev_message(state)

    if not message.from_user:
        answer = await message.answer(UserHandlerMessages.CANT_IDENTIFY_PROFILE)
        await state.update_data(prev_bot_message=answer)
        return

    telegram_chat_id = str(message.from_user.id)

    # User sent /link (initiate linking)
    response = await bp_api.initiate_link(telegram_chat_id)
    if response and response.get("status") == "success":
        token = response.get("token")
        if token:
            answer = await message.answer(
                UserHandlerMessages.LINK_INITIATE_SUCCESS.format(token=token)
            )
        else:
            answer = await message.answer(UserHandlerMessages.LINK_INITIATE_ERROR)
    elif response and response.get("message"):
        answer = await message.answer(response.get("message"))
    else:
        answer = await message.answer(UserHandlerMessages.LINK_INITIATE_ERROR)

    await state.update_data(prev_bot_message=answer)


@user_router.message(Command("help"))
async def help_command(message: Message, state: FSMContext):
    """
    Handler for the /help command.
    """
    await message.delete()
    await delete_prev_message(state)

    answer = await message.answer(UserHandlerMessages.HELP)
    await state.update_data(prev_bot_message=answer)

