import pytest
import pytest_asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler


# A mock bot token for testing
BOT_TOKEN = "123456:ABC-DEF1234567890"

# The secret token for testing
SECRET_TOKEN = "test-secret"


@pytest_asyncio.fixture
async def client(aiohttp_client):
    """Fixture to create an aiohttp client with a configured webhook handler."""
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    app = web.Application()
    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=SECRET_TOKEN,
    )
    handler.register(app, path="/webhook")
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_webhook_no_secret(client):
    """Test that a request without the secret token is rejected."""
    resp = await client.post("/webhook", json={})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_webhook_wrong_secret(client):
    """Test that a request with a wrong secret token is rejected."""
    headers = {"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"}
    resp = await client.post("/webhook", json={}, headers=headers)
    assert resp.status == 401


@pytest.mark.asyncio
async def test_webhook_correct_secret(client):
    """Test that a request with the correct secret token is accepted."""
    headers = {"X-Telegram-Bot-Api-Secret-Token": SECRET_TOKEN}
    # A minimal valid telegram update
    update = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 1,
            "chat": {"id": 1, "type": "private"},
            "text": "test",
        },
    }
    resp = await client.post("/webhook", json=update, headers=headers)
    assert resp.status == 200
