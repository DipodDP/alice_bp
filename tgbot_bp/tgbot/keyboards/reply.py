from enum import Enum
from aiogram.utils.keyboard import ReplyKeyboardBuilder


class ReplyButtons(str, Enum):
    BTN_GET_REPORT = "🧾 Отправить отчет"
    SEND_MENU = '🧾 Show Menu'
    RESERVATION = '🍽 Make Reservation'


class NavButtons(str, Enum):
    BTN_NEXT = "➡️ Дальше"
    BTN_BACK = "↩️ Назад"
    BTN_SEND = "➡️ Отправить"
    BTN_CANCEL = "❌ Отменить"
    BTN_OK = "🆗"


def user_menu_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=ReplyButtons.BTN_GET_REPORT)
    keyboard.adjust()
    return keyboard.as_markup(
        input_field_placeholder=f"Нажмите на кнопку {ReplyButtons.BTN_GET_REPORT.value}",
        one_time_keyboard=True,
        resize_keyboard=True,
    )


def cancel_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_CANCEL)
    keyboard.adjust(1, 2)
    return keyboard.as_markup(
        input_field_placeholder=f"Нажмите {NavButtons.BTN_CANCEL.value} для отмены",
        resize_keyboard=True,
    )


def ok_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_OK)
    keyboard.adjust()
    return keyboard.as_markup(
        input_field_placeholder=f"Нажмите {NavButtons.BTN_OK.value}",
        resize_keyboard=True,
    )


def nav_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text=NavButtons.BTN_BACK)
    keyboard.button(text=NavButtons.BTN_CANCEL)
    keyboard.adjust(2)
    return keyboard.as_markup(
        input_field_placeholder="Введите ответ...", resize_keyboard=True
    )
