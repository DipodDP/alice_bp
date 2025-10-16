from dataclasses import dataclass
from typing import Optional

from environs import Env


WEBHOOK_PATH = "/webhook"


@dataclass
class TgBot:
    """
    Creates the TgBot object from environment variables.
    """

    token: str
    admin_ids: list[int]
    proxy_url: str
    use_redis: bool
    console_log_level: str
    webhook_host: str | None = None
    webapp_host: str | None = None
    webapp_port: int | None = None

    @staticmethod
    def from_env(env: Env):
        """
        Creates the TgBot object from environment variables.
        """
        token = env.str("BOT_TOKEN")
        admin_ids = list(map(int, env.list("ADMINS")))
        console_log_level = env.str("CONSOLE_LOGGER_LVL")
        # admin_ids = list(map(
        #     lambda item: int(item) if isinstance(item, int) else str(item),
        #     env.list("ADMINS")
        # ))
        use_redis = env.bool("USE_REDIS")
        proxy_url = env.str("PROXY_URL", default=None)
        webhook_host = env.str("WEBHOOK_HOST", default=None)
        webapp_host = env.str("WEBAPP_HOST", default=None)
        webapp_port = env.int("WEBAPP_PORT", default=None)
        return TgBot(
            token=token,
            admin_ids=admin_ids,
            use_redis=use_redis,
            console_log_level=console_log_level,
            proxy_url=proxy_url,
            webhook_host=webhook_host,
            webapp_host=webapp_host,
            webapp_port=webapp_port,
        )


@dataclass
class RedisConfig:
    """
    Redis configuration class.

    Attributes
    ----------
    redis_pass : Optional(str)
        The password used to authenticate with Redis.
    redis_port : Optional(int)
        The port where Redis server is listening.
    redis_host : Optional(str)
        The host where Redis server is located.
    """

    redis_pass: Optional[str]
    redis_port: Optional[int]
    redis_host: Optional[str]

    def dsn(self) -> str:
        """
        Constructs and returns a Redis DSN (Data Source Name) for this database configuration.
        """
        if self.redis_pass:
            return f"redis://:{self.redis_pass}@{self.redis_host}:{self.redis_port}/0"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/0"

    @staticmethod
    def from_env(env: Env):
        """
        Creates the RedisConfig object from environment variables.
        """
        redis_pass = env.str("REDIS_PASSWORD")
        redis_port = env.int("REDIS_PORT")
        redis_host = env.str("REDIS_HOST")

        return RedisConfig(
            redis_pass=redis_pass, redis_port=redis_port, redis_host=redis_host
        )


@dataclass
class DjangoApiConfig:
    """
    Django API configuration class.
    """

    base_url: str
    api_token: str | None = None

    @staticmethod
    def from_env(env: Env):
        """
        Creates the DjangoApiConfig object from environment variables.
        """
        base_url = env.str("DJANGO_API_BASE_URL", default="http://localhost:8000")
        api_token = env.str("DJANGO_API_TOKEN", default=None)

        return DjangoApiConfig(
            base_url=base_url,
            api_token=api_token,
        )


@dataclass
class Miscellaneous:
    """
    Miscellaneous configuration class.

    This class holds settings for various other parameters.
    It merely serves as a placeholder for settings that are not part of other categories.

    Attributes
    ----------
    other_params : str, optional
        A string used to hold other various parameters as required (default is None).
    """

    other_params: str | None = None

    @staticmethod
    def from_env(env: Env):
        """
        Creates the Miscellaneous object from environment variables.
        """

        return Miscellaneous()


@dataclass
class Config:
    """
    The main configuration class that integrates all the other configuration classes.

    This class holds the other configuration classes, providing a centralized point of access for all settings.

    Attributes
    ----------
    tg_bot : TgBot
        Holds the settings related to the Telegram Bot.
    misc : Miscellaneous
        Holds the values for miscellaneous settings.
    db : Optional[DbConfig]
        Holds the settings specific to the database (default is None).
    redis : Optional[RedisConfig]
        Holds the settings specific to Redis (default is None).
    django_api : DjangoApiConfig
        Holds the settings specific to Django API.
    """

    tg_bot: TgBot
    misc: Miscellaneous
    redis: Optional[RedisConfig] = None
    django_api: DjangoApiConfig = None


def load_config(path: str | None = None) -> Config:
    """
    This function takes an optional file path as input and returns a Config object.
    :param path: The path of env file from where to load the configuration variables.
    It reads environment variables from a .env file if provided, else from the process environment.
    :return: Config object with attributes set as per environment variables.
    """

    # Create an Env object.
    # The Env object will be used to read environment variables.
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot.from_env(env),
        # redis=RedisConfig.from_env(env),
        misc=Miscellaneous.from_env(env),
        django_api=DjangoApiConfig.from_env(env),
    )
