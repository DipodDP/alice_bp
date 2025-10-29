import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs

from infrastructure.bp_api.api import BloodPressureApi
from tgbot.core.config import WEBHOOK_PATH, Config, load_config
from tgbot.core.logger import setup_logging
from tgbot.dialogs import dialogs
from tgbot.handlers import routers_list
from tgbot.handlers.error import error_router
from tgbot.middlewares.auth import AuthMiddleware
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.misc import notify_admins
from tgbot.misc.setting_comands import set_all_default_commands


def register_global_middlewares(dp: Dispatcher, config: Config):
    """
    Register global middlewares for the given dispatcher.
    Global middlewares here are the ones that are applied to all the handlers (you specify the type of update)

    :param dp: The dispatcher instance.
    :type dp: Dispatcher
    :param config: The configuration object from the loaded configuration.
    :return: None
    """
    middleware_types = [
        ConfigMiddleware(config),
        AuthMiddleware(),
    ]

    for middleware_type in middleware_types:
        dp.message.outer_middleware(middleware_type)
        dp.callback_query.outer_middleware(middleware_type)


def get_storage(config: Config):
    """
    Return storage based on the provided configuration.

    Args:
        config (Config): The configuration object.

    Returns:
        Storage: The storage object based on the configuration.

    """
    if config.tg_bot.use_redis:
        # TODO: If you're using Redis, move the imports to the top of the file!
        from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    else:
        return MemoryStorage()


def exit_gracefully():
    """Gracefully cancel all tasks and stop the event loop."""
    try:
        loop = asyncio.get_event_loop()
        logger.debug("Cancelling tasks...")
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        (task.cancel() for task in tasks)
        asyncio.gather(*tasks, return_exceptions=True)
        loop.close()
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        sys.exit(0)


async def on_startup():
    """Insert code here to run it after start"""

    if url := config.tg_bot.bot_webhook_host:
        await bot.set_webhook(url + WEBHOOK_PATH)
    else:
        await bot.delete_webhook()

    await set_all_default_commands(bot)
    await notify_admins.on_startup(bot, config.tg_bot.admin_ids)


async def on_shutdown():
    """Insert code here to run it before shutdown"""
    logging.warning("Shutting down...")

    await notify_admins.on_shutdown(bot, config.tg_bot.admin_ids)
    
    # Remove webhook and close bot instance (not acceptable in some cases)
    # await bot.delete_webhook()
    # await bot.close()

    # Close DB connection (if used)
    await bot.session.close()
    await dp.storage.close()

    exit_gracefully()
    logging.warning("Bye!")


config = load_config("tgbot_bp/.env")
log_level = config.tg_bot.console_log_level

setup_logging(log_level)
logger = logging.getLogger(__name__)
logger.debug(f"Bot config: {config}")

# Proxy URL with credentials: "protocol://user:password@host:port"
session = AiohttpSession(config.tg_bot.proxy_url) if config.tg_bot.proxy_url else None

bot = Bot(token=config.tg_bot.token, session=session)
dp = Dispatcher(storage=get_storage(config))

bp_api = BloodPressureApi(
    base_url=config.django_api.base_url,
    api_token=config.django_api.api_token,
    proxy=config.tg_bot.proxy_url,
)
dp["bp_api"] = bp_api

dp.include_router(error_router)
dp.include_routers(*routers_list)
dp.include_routers(*dialogs)

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

setup_dialogs(dp)

register_global_middlewares(dp, config)
