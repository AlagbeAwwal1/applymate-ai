import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env first, then read env vars
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "0") == "1"

# Hosts
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h] or ["*"]
# Add Render's hostname automatically if present
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "jobs",
    "docs_app",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "applymate.urls"

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

WSGI_APPLICATION = "applymate.wsgi.application"

# ---- Database: SQLite locally, Supabase Postgres in prod ----
if os.getenv("DATABASE_URL"):
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(
            os.environ["DATABASE_URL"],
            conn_max_age=600,     # works well with pgBouncer
            ssl_require=True
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---- Static & Media ----
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
# Note: Render’s filesystem is ephemeral. For persistent uploads, move to S3 later.

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- CORS / CSRF ----
CORS_ALLOW_ALL_ORIGINS = True  # tighten if needed
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://applymate-ai.vercel.app/",
]
# Add Render origin dynamically (scheme required)
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# ---- DRF ----
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# AI Provider
AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
AI_API_KEY = os.getenv("AI_API_KEY", "")
