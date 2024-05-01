import asyncio
import logging
import re
from asyncio import Task
from datetime import datetime, timedelta

from django.db.models import QuerySet, Q
from django.utils import timezone
from playwright.async_api import async_playwright, Browser, Page, ElementHandle

from common.utils import timer
from monitoring.models import MonitoringLink, MonitoringResult, Parameter

logger = logging.getLogger('monitoring')


class LinkMonitoringProcess:
    TIMEOUT_MILLISECONDS: int = 10000
    TIMEOUT_ATTEMPTS: int = 3
    SCALE_MAP: dict = {
        'K': 1000,
        'M': 1000_000,
    }

    def __init__(self):
        self.params: Parameter = Parameter.objects.first()

    async def run(self, source: str | None = None, date: datetime | None = None):
        if not self.params:
            logger.error('No parameters')
            return
        date: datetime = date or timezone.now()
        source_q: Q = Q()
        if source:
            source_q &= Q(source=source)
        links_to_monitor: QuerySet = MonitoringLink.objects.filter(
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

    async def get_video_count(self, video_count_text):
        match: re.Match | None = re.match(r"(\d+\.?\d*)(K|M)?", video_count_text)
        number: float = float(match.group(1))
        scale: str = match.group(2) or ""
        number *= self.SCALE_MAP.get(scale, 1)
        return int(number)

    async def get_page_content(self, link: MonitoringLink, page: Page):
        element: ElementHandle | None = None
        url: str = link.url
        await page.goto(url)
        await page.wait_for_load_state('domcontentloaded')
        current_attempt: int = 0
        while current_attempt < self.TIMEOUT_ATTEMPTS and not element:
            try:
                element = await page.wait_for_selector(
                    "h2[data-e2e='music-video-count']",
                    timeout=self.TIMEOUT_MILLISECONDS)
            except (TimeoutError, asyncio.TimeoutError):
                logger.error("Timeout wait_for_selector while waiting for {}".format(url))
                current_attempt += 1
        return element

    @timer
    async def process_link(self, browser: Browser, link: MonitoringLink) -> MonitoringResult | None:
        page: Page = await browser.new_page()
        element: ElementHandle | None = await self.get_page_content(link, page)
        if not element:
            logger.error('No element')
            return None
        video_count_text: str | None = await element.text_content()
        video_count: int = await self.get_video_count(video_count_text)
        result: MonitoringResult = MonitoringResult(
            monitoring_link=link,
            video_count=video_count
        )
        link.next_monitoring_date = timezone.now() + timedelta(hours=self.params.min_monitoring_timeout)
        await page.close()
        return result

    @timer
    async def monitor_links(self, links: QuerySet[MonitoringLink]) -> None:
        """Запуск мониторинга"""
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=False)  # headless=True чтоб браузер не открывался
            tasks: list[Task] = [asyncio.create_task(self.process_link(browser, link)) async for link in links]
            if tasks:
                results: tuple = await asyncio.gather(*tasks)
                await MonitoringResult.objects.abulk_create(results)
            await browser.close()
        await MonitoringLink.objects.abulk_update(links, fields=["next_monitoring_date"])
