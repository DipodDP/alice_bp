from enum import StrEnum
from django.conf import settings


class HandlerMessages(StrEnum):
    GREETING = "Здравствуйте! Скажите давление и пульс."
    ERROR_UNPARSED = "Не удалось распознать цифры давления или команду. Попробуйте сказать, например, 'давление 120 на 80'."


class LastMeasurementMessages(StrEnum):
    NO_RECORDS = "Записей пока нет."
    REPLY = "Последняя запись: {systolic} на {diastolic}"
    PULSE = ", пульс {pulse}"


class LinkAccountMessages(StrEnum):
    NO_ID = "Не могу определить ваш идентификатор. Пожалуйста, попробуйте еще раз."
    SUCCESS = "Аккаунты успешно связаны!"
    FAIL = "Не удалось связать аккаунты. Проверьте код или попробуйте получить новый."
    ACCOUNT_LINKING_INSTRUCTIONS = f"Чтобы привязать аккаунт, перейдите в Telegram, найдите бота @{settings.ALICE_BOT_USERNAME} и получите код следуя инструкциям."


class RecordPressureMessages(StrEnum):
    SUCCESS = "Запомнила давление {systolic} на {diastolic}"
    SUCCESS_WITH_PULSE = "Запомнила давление {systolic} на {diastolic}, пульс {pulse}"
    INVALID = (
        "Некорректные значения давления. Пожалуйста, проверьте данные и повторите."
    )


class DateFormattingMessages(StrEnum):
    TODAY = "сегодня"
    YESTERDAY = "вчера"
    DAY_BEFORE_YESTERDAY = "позавчера"
    PREPOSITION = "в"


class SerializerMessages(StrEnum):
    VALIDATION_SYSTOLIC_RANGE = "Systolic must be between {min} and {max}."
    VALIDATION_DIASTOLIC_RANGE = "Diastolic must be between {min} and {max}."
    VALIDATION_SYSTOLIC_GT_DIASTOLIC = "Systolic must be greater than diastolic."
    VALIDATION_PULSE_RANGE = "Pulse must be between {min} and {max}."


class ViewMessages(StrEnum):
    USER_NOT_FOUND = "User not found"
    UNABLE_TO_IDENTIFY_USER = "Не удалось определить пользователя."


class LinkStatusViewMessages(StrEnum):
    LINKED = "Аккаунты успешно связаны."
    NOT_LINKED = "Аккаунты не связаны."


class UnlinkViewMessages(StrEnum):
    SUCCESS = "Аккаунты успешно отвязаны."
    NOT_LINKED = "Аккаунты не были связаны."


class GenerateLinkTokenViewMessages(StrEnum):
    USER_ID_MISSING = "telegram_user_id is missing"
    INVALID_USER_ID = "Invalid telegram_user_id format"
    SUCCESS = "Token generated successfully"
    FAIL = "Failed to generate token"


class ServiceMessages(StrEnum):
    RATE_LIMIT_ERROR = "Too many token generation requests for this user."
