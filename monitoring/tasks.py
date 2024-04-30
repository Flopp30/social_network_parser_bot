import asyncio
import logging
from datetime import datetime
from typing import Optional

from celery import shared_task
from django.utils import timezone
from monitoring.models import MonitoringLink
from monitoring.scrapper import LinkMonitoringProcess

logger = logging.getLogger('monitoring')


@shared_task
def parse_tt_links(source: Optional[str], date: Optional[datetime]):
    scrapper = LinkMonitoringProcess()
    try:
        res = asyncio.run(scrapper.run(source, date))
    except Exception as e:
        logger.error(e)
        res = "with error"
    return res
