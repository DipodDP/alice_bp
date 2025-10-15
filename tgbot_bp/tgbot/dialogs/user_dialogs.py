import logging
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import (
    Back,
    Cancel,
    ScrollingGroup,
    Select,
    Start,
)
from aiogram_dialog.widgets.text import Const, Format, Multi

from tgbot.dialogs.callbacks import (
    selected_interval,
)
from tgbot.dialogs.getters import get_time_interval
from tgbot.dialogs.states import (
    MainMenu,
)
from tgbot.keyboards.reply import NavButtons
from tgbot.messages.dialogs_msg import UserDialogMessages
from tgbot.keyboards.dialog import UserDialogButtons

logger = logging.getLogger(__name__)


async def close_dialog(_, __, dialog_manager: DialogManager, **kwargs):
    await dialog_manager.done()


async def put_start_data_in_dialog(start_data: dict, dialog_manager: DialogManager):
    for key in start_data.keys():
        dialog_manager.dialog_data[key] = start_data[key]
    logger.debug(f"Start data: {start_data, dialog_manager.dialog_data}")


user_menu_dialog = Dialog(
        Window(
        Multi(
            Const(UserDialogMessages.GREETINGS),
            sep="\n\n",
        ),
        Start(
            Const(UserDialogButtons.GET_REPORT),
            id="get_report",
            state=MainMenu.interval_selection,
        ),
        state=MainMenu.main,
    ),

    Window(
        Const(UserDialogMessages.CHOOSE_INTERVAL),
        ScrollingGroup(
            Select(
                id="time_select",
                items="time_slots",
                item_id_getter=lambda item: item.time,
                text=Format("{item.label}"),
                on_click=selected_interval,
            ),
            id="time_group",
            height=4,
            width=2,
            hide_on_single_page=True,
        ),
        Back(Const(NavButtons.BTN_BACK)),
        # Cancel(Const(NavButtons.BTN_BACK), on_click=set_prev_message),
        state=MainMenu.interval_selection,
        getter=get_time_interval,
    ),
    on_process_result=close_dialog,
)
