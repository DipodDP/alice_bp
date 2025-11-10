import logging
from functools import wraps
from aiogram_dialog import DialogManager

from infrastructure.bp_api.base import BaseClient

logger = logging.getLogger(__name__)


def dialog_data_cache(key_prefix: str):
    """
    A decorator to cache the results of an asynchronous function in `dialog_manager.dialog_data`.

    The cache key is constructed using a `key_prefix` and the Telegram user ID.

    This decorator should be used on the data fetching function inside a getter, not on the getter itself.

    Args:
        key_prefix (str): A prefix for the cache key to differentiate cached data
                          when multiple types of data are being cached.

    Returns:
        Callable: A decorator that caches the result of the decorated function.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            dialog_manager: DialogManager, api_client: BaseClient, **kwargs
        ):
            telegram_user_id = str(dialog_manager.event.from_user.id)
            cache_key = f"{key_prefix}_{telegram_user_id}"

            if cache_key in dialog_manager.dialog_data:
                logger.info(f"Returning cached data for {cache_key}")
                return dialog_manager.dialog_data[cache_key]

            result = await func(dialog_manager, api_client, **kwargs)
            dialog_manager.dialog_data[cache_key] = result
            return result

        return wrapper

    return decorator


def clear_dialog_data_cache(key_prefix: str):
    """
    A decorator to clear a specific cached entry from `dialog_manager.dialog_data`
    before the decorated function (e.g., a callback) is executed.

    The cache key is constructed using a `key_prefix` and the Telegram user ID.

    Args:
        key_prefix (str): The prefix used to construct the cache key.

    Returns:
        Callable: A decorator that clears the cache before the decorated function.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(
            callback_query,
            widget,
            dialog_manager: DialogManager,
            item_id: str,
            **kwargs,
        ):
            # Clear the cache first
            telegram_user_id = str(dialog_manager.event.from_user.id)
            cache_key = f"{key_prefix}_{telegram_user_id}"
            if cache_key in dialog_manager.dialog_data:
                del dialog_manager.dialog_data[cache_key]
                logger.debug(f"Cleared cache for {cache_key}")

            # Then execute the original function
            await func(callback_query, widget, dialog_manager, item_id, **kwargs)

        return wrapper

    return decorator
