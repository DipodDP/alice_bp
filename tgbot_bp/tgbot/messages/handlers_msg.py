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
