import os

from celery import Celery
from django.conf import settings
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parserbot.settings')

app = Celery('celery', broker=settings.CELERY_BROKER, backend=settings.CELERY_BACKEND)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(settings.INSTALLED_APPS)

app.conf.task_queues = (
    Queue('default', Exchange('default'), routing_key='default'),
    Queue('long_tasks', Exchange('long_tasks'), routing_key='long_tasks'),
)
