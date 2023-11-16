from pathlib import Path
from environs import Env
import os
import dj_database_url

env = Env()
env.read_env()

# Bot definition
TELEGRAM_TOKEN = env('BOT_TOKEN', None)
BOT_LOG_LEVEL = env('BOT_LOG_LEVEL', 10)
BOT_MODE = env('BOT_MODE', 'callback')  # webhook in other case

# Scrappers definition
TT_SIGNATURE_URL = env('TT_SIGNATURE_URL')
TT_MUSIC_ERROR_ATTEMPTS = env('TT_MUSIC_ERROR_ATTEMPTS', 3)
TT_USER_ERROR_ATTEMPTS = env('TT_USER_ERROR_ATTEMPTS', 3)

# Django definition
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-^j2m)eqo#&8h_(9x3w_c4@kqo3a1=o2-an8_n6xvc)*5qoecbg'

DEBUG = env.bool('DJ_DEBUG', True)

ALLOWED_HOSTS = env.list('DJ_ALLOWED_HOSTS', ['*'])
CSRF_TRUSTED_ORIGINS = env.list('DJ_CSRF_TRUSTED_ORIGINS', [])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # custom
    "bot_parts",
    "user",
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

ROOT_URLCONF = 'parserbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'parserbot.wsgi.application'

DATABASES = {
    'default': dj_database_url.parse(
        env('DJ_DB_URL', 'sqlite:///db.sqlite3'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATIC_DIR = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    STATIC_DIR,
]
STATIC_ROOT = './assets/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


CELERY_BROKER = env('CELERY_BROKER')
CELERY_BACKEND = env('CELERY_BACKEND')
CELERY_IMPORTS = ('parserbot.tasks',)
