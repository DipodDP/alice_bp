from enum import Enum


class AdminHandlerMessages(str, Enum):
    GREETINGS = "Hello, admin! It's Cirulnik admin bot.\nPress /stop to stop bot\nPress /loc to update locations"
    STOPPING = "Stopping bot..."
    ERROR = "Error!\n"


class UserHandlerMessages(str, Enum):
    GREETINGS = "Hello! It's template bot."
    HELP = (
        "🤖 Доступные команды:\n\n"
        "📊 Давление:\n"
        "• Используйте кнопку 'Получить отчет' для просмотра измерений давления\n"
        "• Выберите период: за неделю, за прошлую неделю или за месяц\n\n"
        "ℹ️ Общие:\n"
        "• /help - показать это сообщение\n"
        "• /start - начать работу с ботом"
    )
    CANCEL = "Действие отменено!"
    COMPLETED = "Действие завершено!"
    # Linking flow messages
    START_GREETING = (
        "Здравствуйте! Я бот для синхронизации с вашим аккаунтом в Алисе.\n\n"
        "Чтобы завершить настройку, получите код в навыке Алисы и отправьте мне команду "
        "в формате `/link КОД`."
    )
    LINK_NO_CODE = "Пожалуйста, укажите код после команды. Например: `/link A1B2-C3D4`"
    LINK_SUCCESS = "Аккаунты успешно связаны!"
    LINK_ERROR = "Произошла неизвестная ошибка. Попробуйте получить код еще раз и повторить попытку."
