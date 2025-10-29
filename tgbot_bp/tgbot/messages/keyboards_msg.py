from enum import StrEnum


class ReplyButtons(StrEnum):
    BTN_GET_REPORT = "🧾 Отправить отчет"


class NavButtons(StrEnum):
    BTN_NEXT = "➡️ Дальше"
    BTN_BACK = "↩️ Назад"
    BTN_SEND = "➡️ Отправить"
    BTN_CANCEL = "❌ Отменить"
    BTN_OK = "🆗"


# Input field placeholders
PLACEHOLDER_PRESS_BUTTON = "Нажмите на кнопку {button_text}"
PLACEHOLDER_PRESS_CANCEL = "Нажмите {button_text} для отмены"
PLACEHOLDER_PRESS_OK = "Нажмите {button_text}"
PLACEHOLDER_ENTER_RESPONSE = "Введите ответ..."
