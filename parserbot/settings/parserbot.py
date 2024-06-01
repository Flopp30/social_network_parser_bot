import os

# Bot definition
TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN', None)
BOT_LOG_LEVEL = os.environ.get('BOT_LOG_LEVEL', 10)
BOT_MODE = os.environ.get('BOT_MODE', 'callback')  # webhook in other case
TELEGRAM_DOC_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument'
TELEGRAM_MESSAGE_URL = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'

# Scrappers definition
TT_SIGNATURE_URL = os.environ.get('TT_SIGNATURE_URL')
TT_MUSIC_ERROR_ATTEMPTS = os.environ.get('TT_MUSIC_ERROR_ATTEMPTS', 3)
TT_USER_ERROR_ATTEMPTS = os.environ.get('TT_USER_ERROR_ATTEMPTS', 3)

TIKTOK_MS_TOKEN = os.environ.get('TIKTOK_MS_TOKEN', '').split(';')
