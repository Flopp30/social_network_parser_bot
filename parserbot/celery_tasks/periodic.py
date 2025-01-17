# TODO пока пусть будет так, но вообще их надо будет по приложениям разнести, когда их станет побольше
import asyncio
import logging
from datetime import datetime

from celery.utils.log import get_task_logger
from django.db.models import Count, QuerySet

from common.celery import periodic_celery_task
from common.utils import HttpTelegramMessageSender, adaptive_threshold, analyze_growth
from monitoring.models import MonitoringLink, MonitoringResult, Parameter
from monitoring.process import LinkMonitoringProcess
from user.models import User

logger = logging.getLogger('monitoring')
celery_logger = get_task_logger(__name__)


@periodic_celery_task(name='monitor_links')
def monitor_links(source: MonitoringLink.Sources | None = None, date: datetime | None = None) -> str:
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
    processor = LinkMonitoringProcess(source, date)
    return asyncio.run(processor.run())


@periodic_celery_task(name='cleanup_links')
def delete_redundant_results() -> str:
    """Задача для очистки избыточных результатов мониторинга"""
    params = Parameter.objects.first()

    if not params:
        return "Couldn't delete redundant result without params"

    links_with_redundant_results = MonitoringLink.objects.annotate(result_count=Count('results')).filter(result_count__gt=params.max_monitoring_count)

    for link in links_with_redundant_results:
        ids_to_delete = link.results.all().order_by('created_at').values_list('id', flat=True)[: link.result_count - params.max_monitoring_count]
        link.results.filter(id__in=list(ids_to_delete)).delete()
        logger.info(f'Deleted {len(ids_to_delete)} old results for link {link.url}')

    return 'ok'


def get_chat_ids(params: Parameter) -> list[int]:
    """Возвращает список id для отправки уведомлений в ТГ"""
    id_from_param: list[int] = []
    for id_ in params.chats_id_for_alert.split(','):
        if id_.isdigit():
            id_from_param.append(int(id_))
    id_from_param.extend(User.objects.filter(send_alerts=True).values_list('chat_id', flat=True))
    # id_from_param.extend(map(int, filter(lambda x: x.is_digit(), params.chats_id_for_alert.split(','))))
    return id_from_param


@periodic_celery_task(name='analyze_last_two_results')
def analyze_growth_easy():
    """Делим последнее на предпоследнее"""
    params = Parameter.objects.first()
    if not params:
        return "Couldn't analyze growth without params"
    chat_ids: list[int] = get_chat_ids(params)
    links = MonitoringLink.objects.all()
    for link in links:
        results = MonitoringResult.objects.filter(monitoring_link=link).order_by('-created_at')[:2]
        celery_logger.info(results)
        if len(results) == 2:
            old_count, new_count = results[1].video_count, results[0].video_count
            growth_ratio = new_count / old_count
            if growth_ratio > params.alert_ratio:
                message = (
                    'Внимание!\n'
                    f'Для ссылки {link.url} замечено резкое повышение просмотров с {old_count} до {new_count}!\n'
                    f'Пороговый коэффициент: {params.alert_ratio}'
                )
                celery_logger.info(f'ALERT! Growth ratio for link {link.url}: {growth_ratio}')
                for chat_id in chat_ids:
                    HttpTelegramMessageSender.sync_send_text_message(chat_id, message)
    return 'ok'


@periodic_celery_task(name='analyze_results_weight_calculation')
def analyze_growth_weight() -> str:
    """Ищем взвешенный рост"""
    params: Parameter | None = Parameter.objects.first()
    if not params:
        return "Couldn't analyze growth without params"

    chat_ids: list[int] = get_chat_ids(params)
    links: QuerySet[MonitoringLink] = MonitoringLink.objects.all()
    for link in links:
        video_count_history: list[int] = list(
            MonitoringResult.objects.filter(monitoring_link=link).order_by('-created_at')[: params.max_monitoring_count].values_list('video_count', flat=True),
        )
        video_count_history.reverse()
        celery_logger.info(f'video_count_history {video_count_history}')
        weight_rate = analyze_growth(video_count_history)
        if weight_rate is None:
            return f'Error with link {link}'

        threshold = adaptive_threshold(max(video_count_history))
        if weight_rate > threshold:
            celery_logger.info(
                f'ALERT! Growth weight ratio for link {link.url}: weight_rate {weight_rate} threshold {threshold}',
            )
            message = (
                'Внимание!\n'
                f'Для ссылки {link.url} замечено повышение просмотров!\n'
                f'Взвешенный рост: {weight_rate * 100:.2f}%\n'
                f'Текущий порог: {threshold * 100:.2f}%\n'
                f'Значения, на которых нашлось превышение: {video_count_history} '
            )
            for chat_id in chat_ids:
                HttpTelegramMessageSender.sync_send_text_message(chat_id, message)
    return 'ok'
