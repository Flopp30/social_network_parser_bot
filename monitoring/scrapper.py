import asyncio
import logging
import re

from datetime import datetime, timedelta

from asgiref.sync import sync_to_async
from django.db.models import QuerySet
from django.utils import timezone
from monitoring.models import MonitoringLink, MonitoringResult, Parameter
from playwright.async_api import async_playwright

TIMEOUT_MILLISECONDS = 10000

logger = logging.getLogger('monitoring')


def check_and_parse_links():  # TODO Должно быть задачей для Celery
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


async def create_link(url: str) -> MonitoringLink:
    """Создание ссылки (для бота)"""
    return await MonitoringLink.objects.acreate(
        url=url,
        created_at=timezone.now()
    )


async def monitor_links(links: QuerySet[MonitoringLink]) -> None:
    """Поиск количества клипов"""
    params = None
    timeout_hours = 24
    try:
        params = await Parameter.objects.afirst()
        timeout_hours = params.min_monitoring_timeout
    except Exception:
        logger.warning('No parameters')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headless=True чтоб браузер не открывался
        async for link in links:
            url = link.url
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state('domcontentloaded')
            try:
                element = await page.wait_for_selector("h2[data-e2e='music-video-count']", timeout=TIMEOUT_MILLISECONDS)
            except (TimeoutError, asyncio.TimeoutError):
                logger.error("Timeout wait_for_selector while waiting for {}".format(url))
                continue
            video_count_text = await element.text_content()
            match = re.match(r"(\d+\.?\d*)(K|M)?", video_count_text)
            number = float(match.group(1))
            scale = match.group(2) or ""
            if scale == 'K':
                number *= 1000
            elif scale == 'M':
                number *= 1000000
            video_count = int(number)

            await MonitoringResult.objects.acreate(
                monitoring_link=link,
                video_count=video_count
            )
            await check_links_for_delete(link, params)  # TODO вынести в задачу Celery
            link.next_monitoring_date = timezone.now() + timedelta(hours=timeout_hours)
            await link.asave()

            await page.close()
        await browser.close()


@sync_to_async
def get_ids_to_delete(link, delete_count):  # синхронная выборка, пришлось сделать так
    return list(MonitoringResult.objects.filter(monitoring_link=link)
                .order_by('created_at')
                .values_list('id', flat=True)[:delete_count])


async def check_links_for_delete(link: MonitoringLink, params: Parameter) -> None:
    """Удаляет старые MonitoringResult, если их больше чем max_monitoring_count """
    result_count = await MonitoringResult.objects.filter(monitoring_link=link).acount()
    max_monitoring_count = 10
    if params:
        max_monitoring_count = params.max_monitoring_count
    if result_count > max_monitoring_count:
        delete_count = result_count - max_monitoring_count
        ids_to_delete = await get_ids_to_delete(link, delete_count)
        async for result in MonitoringResult.objects.filter(id__in=list(ids_to_delete)):
            await result.adelete()
