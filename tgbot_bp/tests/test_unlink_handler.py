import pytest

from tgbot.handlers.user import process_unlink_command
from tgbot.messages.handlers_msg import UserHandlerMessages


@pytest.mark.parametrize(
    "api_return_value, fallback_message",
    [
        ({"status": "unlinked", "message": "Аккаунты успешно отвязаны."}, None),
        ({"status": "not_linked", "message": "Аккаунты не были связаны."}, None),
        (None, UserHandlerMessages.UNLINK_ERROR),
        (
            {"status": "error", "unexpected_field": "value"},
            UserHandlerMessages.UNLINK_ERROR,
        ),
    ],
)
@pytest.mark.asyncio
async def test_process_unlink_command_parameterized(
    message_mock, bp_api_mock, api_return_value, fallback_message
):
    """
    Test process_unlink_command with various API responses using parametrization.
    """
    bp_api_mock.unlink_account.return_value = api_return_value

    await process_unlink_command(message_mock, bp_api_mock)

    bp_api_mock.unlink_account.assert_called_once_with(str(message_mock.from_user.id))

    expected_message = (
        api_return_value.get("message")
        if api_return_value and "message" in api_return_value
        else fallback_message
    )
    message_mock.answer.assert_called_once_with(expected_message)
