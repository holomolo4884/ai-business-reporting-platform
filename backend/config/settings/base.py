from pathlib import Path

import environ

# BASE_DIR указывает на папку backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ищем .env сначала в backend/.env, потом в корне проекта/.env
ENV_FILE = BASE_DIR / ".env"

if not ENV_FILE.exists():
    ENV_FILE = BASE_DIR.parent / ".env"

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

env.read_env(ENV_FILE)

# =====================================
# Core Django settings
# =====================================

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
    ],
)

# =====================================
# Applications
# =====================================

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
    "django_filters",
    "drf_spectacular",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",
]

LOCAL_APPS = [
    "accounts",
    "organizations",
    "business_data",
    "metrics",
    "reports",
    "ai",
    "notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =====================================
# Middleware
# =====================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# =====================================
# Database
# =====================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="reporting"),
        "USER": env("POSTGRES_USER", default="reporting"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="reporting"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

# =====================================
# Password validation
# =====================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =====================================
# Internationalization
# =====================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# =====================================
# Static files
# =====================================

STATIC_URL = "static/"

# =====================================
# Default primary key field type
# =====================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =====================================
# Custom User Model
# =====================================

AUTH_USER_MODEL = "accounts.User"

# =====================================
# Django REST Framework
# =====================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# =====================================
# drf-spectacular
# =====================================

SPECTACULAR_SETTINGS = {
    "TITLE": "AI Business Reporting Platform API",
    "DESCRIPTION": "API for AI-powered business reporting platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
}

# =====================================
# CORS
# =====================================

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[],
)

# В dev-режиме разрешаем все origins
# В prod нужно явно указывать разрешённые домены
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# =====================================
# Redis / Cache
# =====================================

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "reporting",
    }
}

# =====================================
# Celery
# =====================================

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# =====================================
# Simple JWT
# =====================================

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# =====================================
# Media files
# =====================================

import os  # noqa: E402

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# =====================================
# AI Integration Settings
# =====================================

# Провайдер: fake, gigachat, openai
AI_PROVIDER = os.environ.get("AI_PROVIDER", "fake")

# Авторизационный ключ (credentials) для GigaChat API
# или API ключ для OpenAI
AI_API_KEY = os.environ.get("AI_API_KEY", "")

# Модель AI
# Для GigaChat: GigaChat, GigaChat-Pro, GigaChat-Max, GigaChat-2
# Для OpenAI: gpt-4, gpt-3.5-turbo
AI_MODEL = os.environ.get("AI_MODEL", "GigaChat")

# Область применения для GigaChat:
# GIGACHAT_API_PERS, GIGACHAT_API_B2B, GIGACHAT_API_CORP
AI_SCOPE = os.environ.get("AI_SCOPE", "GIGACHAT_API_PERS")

# Таймаут запроса к AI (секунды)
AI_TIMEOUT_SECONDS = int(os.environ.get("AI_TIMEOUT_SECONDS", "60"))

# Максимальное количество попыток при ошибке
AI_MAX_RETRIES = int(os.environ.get("AI_MAX_RETRIES", "3"))

# Проверка SSL сертификатов для GigaChat
# False для разработки, True для продакшена
AI_VERIFY_SSL = os.environ.get("AI_VERIFY_SSL", "False").lower() == "true"

# Температура генерации (0.0 - 1.0)
# 0 = детерминированный ответ, 1 = более креативный
AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", "0.7"))

# Максимальное количество токенов в ответе
AI_MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", "2000"))
