import os

from parserbot.settings import DEBUG

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} | {filename}>{funcName}():{lineno} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '{asctime} {levelname} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'include_html': True,
        #     'filters': ['require_debug_false']
        # },
        'debug_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.environ.get('DEBUG_LOG', './logs/django-debug.log'),
            'filters': ['require_debug_true'],
        },
        'errors_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.environ.get('ERROR_LOG', './logs/django-error.log'),
            'when': 'MIDNIGHT',
            'backupCount': 7,
            'formatter': 'verbose',
        },
        'base_log': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.environ.get('BASE_LOG', './logs/django-base.log'),
            'when': 'MIDNIGHT',
            'backupCount': 7,
            'formatter': 'verbose',
        },
        'base_log_warning': {
            'level': 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.environ.get('BASE_LOG', './logs/django-base.log'),
            'when': 'MIDNIGHT',
            'backupCount': 7,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['console', 'errors_file', 'base_log'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'errors_file', 'base_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True,
        },
        'django.server': {
            'level': 'INFO',
            'handlers': ['console', 'base_log_warning'],
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'errors_file', 'base_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'tiktok_scrapper': {
            'handlers': ['console', 'errors_file', 'base_log'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {
            'level': 'INFO',
            'handlers': ['console', 'base_log', 'errors_file'],
            'propagate': True,
        },
    },
}

if DEBUG:
    null_handler = {'class': 'logging.NullHandler'}

    handlers_to_null = [
        'errors_file',
        'base_log',
        'base_log_warning',
        'debug_file',
    ]

    for handler in handlers_to_null:
        LOGGING['handlers'][handler] = null_handler  # type: ignore
