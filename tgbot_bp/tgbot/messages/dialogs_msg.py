from enum import Enum


class UserDialogMessages(str, Enum):
    GREETINGS = "Выберите действие:"
    CHOOSE_INTERVAL = "Выберите отчет:"
    CONTINUE = "Продолжить"
