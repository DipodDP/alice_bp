import logging
import subprocess
from typing import Dict

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

process = None

# Headers that must NOT be forwarded from proxied response to client (hop-by-hop)
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "server",
    "date",
}


def home(request):
    """
    Minimal status page for the external bot subprocess:
    - "alive" if subprocess is running
    - "stopped with code ..." if subprocess exited
    - "down" if no subprocess exists
    """
    global process
    if process:
        status = process.poll()
        if status is None:
            result = "alive! :)"
        else:
            start_url = reverse("app_start")
            result = (
                f"stopped with code {status}. Press <a href='{start_url}'>Start</a>"
            )
    else:
        start_url = reverse("app_start")
        result = f"down! :(. Press <a href='{start_url}'>Start</a>"
    return HttpResponse(f"<h1>App is {result}</h1>")


def start(request):
    """
    Start external bot subprocess (python tgbot_bp/main.py <SITE_URL>).
    NOTE: starting subprocesses from a web worker is fragile in multi-worker setups.
    Prefer running this via systemd / supervisor / management command under a single process.
    """
    global process
    status = "Down"
    if process:
        status = process.poll()

    if status is not None:
        site_url = getattr(settings, "SITE_URL", None)
        if not site_url:
            logger.error("SITE_URL is not configured in Django settings.")
            return HttpResponse(
                "SITE_URL is not configured in Django settings.", status=500
            )

        # Launch the external script and keep subprocess handle in global 'process'
        try:
            cwd = getattr(settings, "BASE_DIR", None)
            # open logs to files (optional) or use PIPEs
            # stdout = open(os.path.join(cwd, "uv_stdout.log"), "a", buffering=1)
            # stderr = open(os.path.join(cwd, "uv_stderr.log"), "a", buffering=1)

            cmd = ["uv", "run", "tgbot_bp/main.py", site_url]
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                #    stdout=stdout,
                #    stderr=stderr,
                #    start_new_session=True,  # detach signals on POSIX
            )
            logger.info(
                "Started main.py subprocess (pid=%s) with SITE_URL=%s",
                getattr(process, "pid", None),
                site_url,
            )
        except Exception as e:
            logger.exception("Failed to start subprocess: %s", e)
            return HttpResponse(f"Failed to start subprocess: {e}", status=500)

    return redirect("app_home")


@csrf_exempt
def webhook_handler(request):
    """
    Proxy incoming webhook to the local  server:

    - Forwards method, headers (except Host), query params, body and cookies.
    - Returns proxied response to caller, filtering hop-by-hop headers.
    - Uses a timeout and handles connection errors gracefully.
    """
    try:
        webhook_path = getattr(settings, "WEBHOOK_PATH", "/webhook")
        webapp_host = getattr(settings, "WEBAPP_HOST", "localhost")
        webapp_port = getattr(settings, "WEBAPP_PORT", 8080)
        local_url = f"http://{webapp_host}:{webapp_port}{webhook_path}"
        logger.debug(f"Incoming headers: {request.headers}")
        query = request.META.get("QUERY_STRING", "")
        if query:
            local_url = f"{local_url}?{query}"

        # Build headers for requests, skip 'Host' so requests sets correct Host for local target
        headers: Dict[str, str] = {
            k: v for k, v in request.headers.items() if k.lower() != "host"
        }

        # Forward cookies and body; for GET/HEAD no body is sent.
        cookies = request.COOKIES or {}
        data = request.body if request.method.upper() not in ("GET", "HEAD") else None

        try:
            proxy_timeout = getattr(settings, "PROXY_TIMEOUT", 15)
            proxied = requests.request(
                method=request.method,
                url=local_url,
                headers=headers,
                params=request.GET.dict(),
                data=data,
                cookies=cookies,
                allow_redirects=False,
                timeout=proxy_timeout,
            )
            logger.debug("Proxying request to %s: %s", local_url, proxied)
        except RequestException as exc:
            logger.exception("Error proxying request to %s: %s", local_url, exc)
            return HttpResponse(f"Proxy error: {exc}", status=502)

        content_type = proxied.headers.get("Content-Type", "")
        # Build Django response from proxied response
        if "application/json" in (content_type or ""):
            try:
                data_json = proxied.json()
                # JsonResponse requires safe=False for non-dict JSON (lists etc.)
                response = JsonResponse(data_json, safe=isinstance(data_json, dict))
            except Exception:
                # Fallback to raw body if JSON parsing fails
                response = HttpResponse(proxied.content, content_type=content_type)
        else:
            response = HttpResponse(
                proxied.content, content_type=content_type or "application/octet-stream"
            )

        response.status_code = proxied.status_code

        # Copy proxied headers except hop-by-hop ones
        for key, value in proxied.headers.items():
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            # Avoid overwriting Content-Type set above unnecessarily
            if key.lower() == "content-type":
                continue
            response[key] = value

        return response
    except Exception as e:
        logger.exception("An unexpected error occurred in webhook_handler: %s", e)
        return HttpResponse("An unexpected error occurred.", status=500)
