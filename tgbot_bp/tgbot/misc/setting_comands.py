from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


DEF_COMMANDS = {
    'ru': [
        BotCommand(command='/start', description='Запустить бота'),
        BotCommand(command='/link', description='Связать аккаунт'),
        BotCommand(command='/unlink', description='Отвязать аккаунт'),
        BotCommand(command='/help', description='Помощь по боту')
    ],
    'en': [
        BotCommand(command='/start', description='Start bot'),
        BotCommand(command='/link', description='Link account'),
        BotCommand(command='/unlink', description='Unlink account'),
        BotCommand(command='/help', description='Bot help')
    ]
}


async def set_all_default_commands(bot: Bot):

    for language_code, commands in DEF_COMMANDS.items():
        await bot.set_my_commands(
            commands=commands,
            scope=BotCommandScopeDefault(),
            language_code=language_code
        )
