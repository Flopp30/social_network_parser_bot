import asyncio
import logging
import re

from datetime import datetime, timedelta
from typing import Optional

from asgiref.sync import sync_to_async
from django.db.models import QuerySet, Q
from django.utils import timezone

from common.utils import timer
from common.validators import LinkValidator
from monitoring.models import MonitoringLink, MonitoringResult, Parameter
from playwright.async_api import async_playwright, Browser


logger = logging.getLogger('monitoring')


class LinkMonitoringProcess:
    TIMEOUT_MILLISECONDS = 10000
    TIMEOUT_ATTEMPTS = 3

    async def run(self, source: Optional[str] = None, date: Optional[datetime] = None):
        date = date or timezone.now()
        source_q = Q()
        if source:
            source_q &= Q(source=source)
        links_to_monitor = MonitoringLink.objects.filter(
            source_q,
            next_monitoring_date__lte=date,
            is_active=True
        )
        if not await links_to_monitor.aexists():
            logger.warning('No links to monitor')
            res = "No links to monitor"
            return res
        try:
            res = await self.monitor_links(links_to_monitor)
        except Exception as e:
            logger.error(e)
            res = "with error"
        return res

    @timer
    async def process_link(self, browser: Browser, params: Optional[Parameter], timeout_hours: int,
                           link: MonitoringLink) -> None:
        url = link.url
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        current_attempt = 0
        while current_attempt < self.TIMEOUT_ATTEMPTS:
            try:
                element = await page.wait_for_selector(
                    "h2[data-e2e='music-video-count']",
                    timeout=self.TIMEOUT_MILLISECONDS)
            except (TimeoutError, asyncio.TimeoutError):
                logger.error("Timeout wait_for_selector while waiting for {}".format(url))
                current_attempt += 1
        scale_map = {
            'K': 1000,
            'M': 1000_000,
        }
        video_count_text = await element.text_content()
        match = re.match(r"(\d+\.?\d*)(K|M)?", video_count_text)
        number = float(match.group(1))
        scale = match.group(2) or ""
        number *= scale_map.get(scale, 1)
        video_count = int(number)
        await MonitoringResult.objects.acreate(
            monitoring_link=link,
            video_count=video_count
        )
        await self.check_links_for_delete(link, params)  # TODO вынести в задачу Celery
        link.next_monitoring_date = timezone.now() + timedelta(hours=timeout_hours)
        await link.asave()
        await page.close()

    @timer
    async def monitor_links(self, links: QuerySet[MonitoringLink]) -> None:
        """Запуск мониторинга"""
        params = None
        timeout_hours = 24
        try:
            params = await Parameter.objects.afirst()
            timeout_hours = params.min_monitoring_timeout
        except Exception:
            logger.warning('No parameters')
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # headless=True чтоб браузер не открывался
            tasks = [asyncio.create_task(self.process_link(browser, params, timeout_hours, link))
                     async for link in links]
            if tasks:
                await asyncio.gather(*tasks)
            await browser.close()

    @sync_to_async
    def get_ids_to_delete(self, link: MonitoringLink, delete_count: int) -> list[int]:
        return list(MonitoringResult.objects.filter(monitoring_link=link)
                    .order_by('created_at')
                    .values_list('id', flat=True)[:delete_count])

    async def check_links_for_delete(self, link: MonitoringLink, params: Optional[Parameter]) -> None:
        """Удаляет старые MonitoringResult, если их больше чем max_monitoring_count """
        result_count = await MonitoringResult.objects.filter(monitoring_link=link).acount()
        max_monitoring_count = 10
        if params:
            max_monitoring_count = params.max_monitoring_count
        if result_count > max_monitoring_count:
            delete_count = result_count - max_monitoring_count
            ids_to_delete = await self.get_ids_to_delete(link, delete_count)
            async for result in MonitoringResult.objects.filter(id__in=list(ids_to_delete)):
                await result.adelete()
