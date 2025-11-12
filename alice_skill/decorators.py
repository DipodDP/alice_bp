from functools import wraps
from django.http import HttpResponseForbidden
from django.conf import settings


def secret_token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        secret = request.headers.get('X-Secret-Token')
        expected_secret = getattr(settings, 'ALICE_WEBHOOK_SECRET', None)

        if not expected_secret or not secret or secret != expected_secret:
            return HttpResponseForbidden('Invalid secret token.')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
