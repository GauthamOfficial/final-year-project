"""
Django settings for the LankaGuide AI project.

LankaGuide AI — AI-Powered Immersive Tourism Companion for Sri Lanka.
See `LankaGuide_AI_PRD.md` (Section 6 & 13) for the full architectural rationale.

This file follows the layout proposed in **Prompt 1A** of the PRD's Cursor AI
Development Plan: MySQL via `django-environ`, CORS for the Next.js client on
`localhost:3000`, DRF wired in, and Redis-backed caching ready for the RAG layer.
"""

from pathlib import Path

import environ

# ───────────────────────── Paths ───────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ───────────────────────── Environment ─────────────────────────────────
# Load values from a `.env` file at the project root. Anything not declared
# in the env file falls back to the default supplied to `env()` below.
env = environ.Env(
    DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    USE_SQLITE_FALLBACK=(bool, True),
    CORS_ALLOWED_ORIGINS=(
        list,
        ["http://localhost:3000", "http://127.0.0.1:3000"],
    ),
    REDIS_URL=(str, "redis://127.0.0.1:6379/1"),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

# ───────────────────────── Security ────────────────────────────────────
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-1x@wf$dyqapa+*rxzl64!_z1qz)#onricnojde1)8tl8@o-urn",
)

DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

# ───────────────────────── Applications ────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.core",
    "apps.attractions",
    "apps.chat",
    "apps.itinerary",
    "apps.vision",
    "apps.sentiment",
    "apps.alerts",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "lankaguide.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "lankaguide.wsgi.application"
ASGI_APPLICATION = "lankaguide.asgi.application"

# ───────────────────────── Database ────────────────────────────────────
# Production target is MySQL (PRD Section 7). For local bring-up before MySQL
# is available we fall back to SQLite when `USE_SQLITE_FALLBACK=true` and no
# `DB_HOST` is configured. Toggle via the `.env` file.
if env("USE_SQLITE_FALLBACK") and not env("DB_HOST", default=""):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": env("DB_NAME", default="lankaguide"),
            "USER": env("DB_USER", default="lankaguide_user"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="127.0.0.1"),
            "PORT": env("DB_PORT", default="3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            "CONN_MAX_AGE": 60,
        }
    }

# ───────────────────────── Cache (Redis) ───────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "lankaguide",
        "TIMEOUT": 60 * 15,
    }
}
DJANGO_REDIS_IGNORE_EXCEPTIONS = True

# ───────────────────────── Authentication ──────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ───────────────────────── Internationalization ────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Colombo"
USE_I18N = True
USE_TZ = True

# ───────────────────────── Static & Media ──────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ───────────────────────── REST Framework ──────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ───────────────────────── CORS (Next.js client) ───────────────────────
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
# The Next.js client passes the anonymous session via this custom header.
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-session-token",
]

# ───────────────────────── External Services ───────────────────────────
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_CHAT_MODEL = env("GEMINI_CHAT_MODEL", default="gemini-1.5-flash")
GEMINI_PRO_MODEL = env("GEMINI_PRO_MODEL", default="gemini-1.5-pro")
GEMINI_EMBEDDING_MODEL = env(
    "GEMINI_EMBEDDING_MODEL", default="models/text-embedding-004"
)

CHROMA_PERSIST_DIR = env(
    "CHROMA_PERSIST_DIR", default=str(BASE_DIR / "var" / "chroma")
)
CHROMA_COLLECTION = env("CHROMA_COLLECTION", default="sri_lanka_tourism")

KAFKA_BOOTSTRAP_SERVERS = env(
    "KAFKA_BOOTSTRAP_SERVERS", default="127.0.0.1:9092"
).split(",")
KAFKA_TOPIC_RAW_REVIEWS = env("KAFKA_TOPIC_RAW_REVIEWS", default="raw_reviews")
KAFKA_TOPIC_SENTIMENT_DONE = env(
    "KAFKA_TOPIC_SENTIMENT_DONE", default="sentiment_done"
)

# ───────────────────────── Logging ─────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "lankaguide": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
    },
}
