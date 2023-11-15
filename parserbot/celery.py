import os
from celery import Celery
from django.conf import settings

# standart code for Celery in Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parserbot.settings')

app = Celery('parserbot', broker=settings.CELERY_BROKER, backend=settings.CELERY_BACKEND)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(settings.INSTALLED_APPS)
