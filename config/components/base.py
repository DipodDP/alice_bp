import os


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-g!vb&)u#oa-zlerg68nyo(esv4^j(_=rtwd9ktf14=ken0#q_("
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv(key="ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    key="CSRF_TRUSTED_ORIGINS", default="http://localhost,http://127.0.0.1"
).split(",")


ALICE_WEBHOOK_SECRET = os.environ.get("ALICE_WEBHOOK_SECRET")


ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
