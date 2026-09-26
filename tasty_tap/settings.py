import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
env_path = BASE_DIR / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-tasty-tap-marketplace-secret-key-2026-secure'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    '127.0.0.1,localhost,testserver,*'
).split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third-party
    'rest_framework',
    # Tasty Tap Apps
    'core',
    'accounts',
    'businesses',
    'restaurants',
    'menu',
    'cart',
    'orders',
    'payments',
    'delivery',
    'reviews',
    'offers',
    'recommendations',
    'notifications',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tasty_tap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.tasty_tap_global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'tasty_tap.wsgi.application'
ASGI_APPLICATION = 'tasty_tap.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': BASE_DIR / os.environ.get('DB_NAME', 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'en-in'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Security & Session settings
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
}

# Tasty Tap Platform Configuration
TASTY_TAP_CONFIG = {
    'JOINING_COST_INR': 0,
    'REGISTRATION_FEE_INR': 0,
    'DEFAULT_DELIVERY_FEE': 25,
    'FREE_DELIVERY_THRESHOLD': 199,
    'TAX_RATE_PERCENT': 5,
    'POINTS_PER_100_INR': 10,
    'POINT_VALUE_INR': 1,
}

# Built-in Tasty Tap Maps API Key & Tile Engine Configuration
MAPS_API_KEY = os.environ.get(
    'MAPS_API_KEY',
    'tt_maps_live_9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c'
)
MAPS_PROVIDER = os.environ.get('MAPS_PROVIDER', 'tasty_tap_tile_engine')

