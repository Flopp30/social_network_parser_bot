import asyncio
import logging
from datetime import datetime
from typing import Optional

from celery import shared_task
from django.db.models import Count

from monitoring.models import Parameter, MonitoringResult, MonitoringLink
from monitoring.process import LinkMonitoringProcess

logger = logging.getLogger('monitoring')


@shared_task
def monitor_links(source: Optional[str], date: Optional[datetime]):
    """
    Задача для мониторинга ссылок. Использует класс мониторинга
    `LinkMonitoringProcess` для получения результатов мониторинга.

    Args:
        source (Optional[str]): Источник ссылок для мониторинга ('youtube', 'tiktok'). Может быть None, в этом случае мониторинг
                                проводится для всех доступных источников.
        date (Optional[datetime]): Дата, на которую должен быть проведен мониторинг. Если None, мониторинг
                                   проводится на текущую дату.

    Returns:
        str: результат мониторинга в виде строки. Может быть "with error" в случае возникновения исключения.
    """
    processor = LinkMonitoringProcess()
    try:
        res = asyncio.run(processor.run(source, date))
    except Exception as e:
        logger.error(e)
        res = "with error"
    return res


@shared_task(name='cleanup_links')
def delete_redundant_results():
    """Задача для очистки избыточных результатов мониторинга"""
    params = Parameter.objects.first()
    if not params:
        logger.error("Couldn't delete redundant result without params")
        return
    links_with_redundant_results = (
        MonitoringLink.objects
        .annotate(result_count=Count('results'))
        .filter(result_count__gt=params.max_monitoring_count)
    )
    for link in links_with_redundant_results:
        ids_to_delete = (
            link.results.all()
            .order_by('created_at')
            .values_list('id', flat=True)
            [:link.result_count - params.max_monitoring_count]
        )
        link.results.filter(id__in=list(ids_to_delete)).delete()
        logger.info(f"Deleted {len(ids_to_delete)} old results for link {link.url}")

