from enum import Enum


class AdminHandlerMessages(str, Enum):
    GREETINGS = "Hello, admin! It's Cirulnik admin bot.\nPress /stop to stop bot\nPress /loc to update locations"
    STOPPING = "Stopping bot..."
    ERROR = "Error!\n"


class UserHandlerMessages(str, Enum):
    GREETINGS = "Hello! It's template bot."
    HELP = "Try some commands from menu"
    CANCEL = "Действие отменено!"
    COMPLETED = "Действие завершено!"
