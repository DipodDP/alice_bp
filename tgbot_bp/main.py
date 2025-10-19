import asyncio
import sys

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp.web_app import Application
from tgbot.core.loader import logger, dp, bot, config, WEBHOOK_PATH
from aiohttp import web

from infrastructure.bp_api.api import BloodPressureApi


async def on_startup(bot, base_url):
    await bot.set_webhook(base_url + WEBHOOK_PATH)


def main():
    # Create an API client instance
    bp_api = BloodPressureApi(base_url=config.django_api.base_url, api_token=config.django_api.api_token)

    # Pass the API client to the dispatcher context
    dp["bp_api"] = bp_api

    # Override webhook host url from env by url from cli
    if len(sys.argv) > 1:
        setattr(config.tg_bot, 'webhook_host', sys.argv[1])

    if url := config.tg_bot.webhook_host:
        logger.info(f'Using webhook: {url + WEBHOOK_PATH}')
        run_webhook_server(bp_api)

    else:
        logger.info('Using long polling...')
        asyncio.run(run_polling(bp_api))


def run_webhook_server(bp_api: BloodPressureApi):
    app = Application()
    app["bp_api"] = bp_api

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    ).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(
        app, host=config.tg_bot.webapp_host, port=config.tg_bot.webapp_port
    )


async def run_polling(bp_api: BloodPressureApi):
    dp["bp_api"] = bp_api
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.warning('Bot is stopped!')
