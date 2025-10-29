import logging
from multiprocessing import Process
from time import sleep
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

STARTUP_PATH = getattr(settings, "STARTUP_PATH", "/start")
INTERVAL = getattr(settings, "STARTUP_INTERVAL", 60 * 30)  # default 30 minutes


def request_startup_url(url: str) -> None:
    """Single startup request (with simple retry on non-200/302)."""
    response = requests.get(url)
    status_code = response.status_code
    logger.info("Requested %s, status code: %s", url, status_code)
    sleep(5)
    if status_code not in (200, 302):
        logger.warning("Status %s for %s, retrying...", status_code, url)
        request_startup_url(url)


def request_url_periodically(url: str, interval: int) -> None:
    """Runs an initial ping, then an infinite loop of pings with the configured interval."""
    request_startup_url(url)
    while True:
        try:
            sleep(interval)
            response = requests.get(url)
            logger.info("Requested %s, status code: %s", url, response.status_code)
        except Exception as e:
            logger.exception("Error while requesting %s: %s", url, e)


def start_requester_process(site_url: str) -> Process:
    """
    Starts a background process that pings SITE_URL + STARTUP_PATH.
    Returns the Process object (so caller can keep reference/manage it).
    """
    target_url = site_url.rstrip("/") + STARTUP_PATH
    requester_process = Process(target=request_url_periodically, args=(target_url, INTERVAL))
    requester_process.daemon = True
    requester_process.start()
    logger.info("Started requester process (pid=%s) for %s", requester_process.pid, target_url)
    return requester_process
