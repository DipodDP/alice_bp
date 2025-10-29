from aiogram.utils.keyboard import ReplyKeyboardBuilder
from tgbot.messages.keyboards_msg import (
    ReplyButtons, 
    NavButtons, 
    PLACEHOLDER_PRESS_BUTTON, 
    PLACEHOLDER_PRESS_CANCEL, 
    PLACEHOLDER_PRESS_OK, 
    PLACEHOLDER_ENTER_RESPONSE
)


def user_menu_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=ReplyButtons.BTN_GET_REPORT)
    keyboard.adjust()
    return keyboard.as_markup(
        input_field_placeholder=PLACEHOLDER_PRESS_BUTTON.format(button_text=ReplyButtons.BTN_GET_REPORT),
        one_time_keyboard=True,
        resize_keyboard=True,
    )


def cancel_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_CANCEL)
    keyboard.adjust(1, 2)
    return keyboard.as_markup(
        input_field_placeholder=PLACEHOLDER_PRESS_CANCEL.format(button_text=NavButtons.BTN_CANCEL),
        resize_keyboard=True,
    )


def ok_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_OK)
    keyboard.adjust()
    return keyboard.as_markup(
        input_field_placeholder=PLACEHOLDER_PRESS_OK.format(button_text=NavButtons.BTN_OK),
        resize_keyboard=True,
    )


def nav_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_BACK)
    keyboard.button(text=NavButtons.BTN_CANCEL)
    keyboard.adjust(2)
    return keyboard.as_markup(
        input_field_placeholder=PLACEHOLDER_ENTER_RESPONSE, resize_keyboard=True
    )
