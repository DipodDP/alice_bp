import betterlogging as bl
from betterlogging.colorized import logging as bl_logging
from betterlogging import logging as std_logging


def setup_logging(log_level: str):
    """
    Set up logging configuration for the application.

    This method initializes the logging configuration for the application.
    It sets the log level to INFO and configures a basic colorized log for
    output. The log format includes the filename, line number, log level,
    timestamp, logger name, and log message.

    Returns:
        None

    Example usage:
        setup_logging()
    """
    if log_level.lower() == 'debug':
        logging = bl_logging
        bl.basic_colorized_config(level=log_level)
    else:
        logging = std_logging

    logging.basicConfig(
        level=log_level,
        format='%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    logger.info(f'Logger level: {log_level}')
    logger.info('Starting bot')
