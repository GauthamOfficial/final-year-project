"""
Django settings for the LankaGuide AI project.

LankaGuide is an AI-powered tourism companion for Sri Lanka — RAG-grounded
chat, itinerary generation, gallery, voice, translation, weather, and
drive-time estimates, all driven from a curated 25-district knowledge base.
"""

from datetime import timedelta
from pathlib import Path

import environ

# ───────────────────────── Paths ───────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ───────────────────────── Environment ─────────────────────────────────
env = environ.Env(
    DEBUG=(bool, True),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    USE_SQLITE_FALLBACK=(bool, False),
    CORS_ALLOWED_ORIGINS=(
        list,
        ["http://localhost:3000", "http://127.0.0.1:3000"],
    ),
    REDIS_URL=(str, "redis://127.0.0.1:6379/1"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
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
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.core",
    "apps.attractions",
    "apps.chat",
    "apps.itinerary",
    "apps.vision",
    "apps.sentiment",
    "apps.alerts",
    "apps.analytics",
    "apps.weather",
    "apps.routing",
    "apps.translation",
    "apps.admin_api",
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
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

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

# ───────────────────────── REST Framework + JWT ────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
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

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
}

# ───────────────────────── CORS (Next.js client) ───────────────────────
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOWED_ORIGIN_REGEXES = []
if DEBUG:
    CORS_ALLOWED_ORIGIN_REGEXES.extend(
        [
            r"^http://127\.0\.0\.1(:\d{1,5})?$",
            r"^http://localhost(:\d{1,5})?$",
            r"^http://\[::1\](:\d{1,5})?$",
        ]
    )
CORS_ALLOW_CREDENTIALS = True
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
]

# ───────────────────────── External Services ───────────────────────────
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
# OpenStreetMap Nominatim (free, no key) — used to resolve POIs to Wikipedia articles.
# See https://operations.osmfoundation.org/policies/nominatim/ — set a real contact in production.
NOMINATIM_BASE_URL = env(
    "NOMINATIM_BASE_URL", default="https://nominatim.openstreetmap.org"
)
NOMINATIM_USER_AGENT = env(
    "NOMINATIM_USER_AGENT",
    default="LankaGuide-AI/1.0 (research project; configure contact email in .env)",
)
# Wikipedia edition for extracts when using `Attraction.wikipedia_title` or Nominatim `wikipedia` tags.
WIKIPEDIA_LANG = env("WIKIPEDIA_LANG", default="en")
GEMINI_CHAT_MODEL = env("GEMINI_CHAT_MODEL", default="gemini-2.5-flash")
GEMINI_PRO_MODEL = env("GEMINI_PRO_MODEL", default="gemini-2.5-pro")
GEMINI_EMBEDDING_MODEL = env(
    "GEMINI_EMBEDDING_MODEL", default="gemini-embedding-001"
)
# Landmark photo ID (`VisionService`); defaults to the same multimodal model as chat.
VISION_GEMINI_MODEL = env("VISION_GEMINI_MODEL", default=GEMINI_CHAT_MODEL)
# Itinerary RAG generation uses this model (JSON itineraries); override via .env.
ITINERARY_RAG_MODEL = env("ITINERARY_RAG_MODEL", default="gemini-1.5-pro")
# Short weather-advisory blurbs for synced SafetyAlert rows (Gemini vision-free).
WEATHER_ALERT_GEMINI_MODEL = env(
    "WEATHER_ALERT_GEMINI_MODEL", default="gemini-1.5-flash"
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

# Google OAuth (used by apps.accounts.views.GoogleAuthView)
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID", default="")
GOOGLE_OAUTH_CLIENT_SECRET = env("GOOGLE_OAUTH_CLIENT_SECRET", default="")

# OpenWeatherMap (free tier) for the weather widget
OPENWEATHER_API_KEY = (env("OPENWEATHER_API_KEY", default="") or "").strip()

# Public OSRM endpoint for drive-time estimates
OSRM_BASE_URL = env(
    "OSRM_BASE_URL", default="https://router.project-osrm.org"
)

# Frontend URL (used in transactional emails / share links)
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@localhost")
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
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
