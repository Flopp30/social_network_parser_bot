import asyncio
import logging

from celery import shared_task
from django.utils import timezone
from monitoring.models import MonitoringLink
from monitoring.scrapper import monitor_links


logger = logging.getLogger('monitoring')


@shared_task
def check_and_parse_links():
    links_to_monitor = MonitoringLink.objects.filter(next_monitoring_date__lte=timezone.now())
    if not links_to_monitor.aexists():
        logger.warning('No links to monitor')
        res = "No links to monitor"
        return res
    try:
        res = asyncio.run(monitor_links(links_to_monitor))
    except Exception as e:
        logger.error(e)
        res = "with error"
    return res
