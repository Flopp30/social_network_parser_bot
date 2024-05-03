import asyncio
import logging
import re
from asyncio import Task
from datetime import datetime, timedelta

from django.db.models import QuerySet, Q
from django.utils import timezone
from playwright.async_api import async_playwright, Browser, Page, ElementHandle, BrowserContext

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
        """Инициализирует атрибут params объекта первой(и единственной) записью из модели Parameter"""
        self.params: Parameter = Parameter.objects.first()
        # self.tiktok_links: QuerySet[MonitoringLink] | None = None
        # self.youtube_links: QuerySet[MonitoringLink] | None = None

    async def run(self, source: str | None = None, date: datetime | None = None):
        """
        Запускает процесс мониторинга ссылок, основываясь на указанном источнике и дате.

        Args:
            source (str | None): Источник ссылок для мониторинга ('youtube', 'tiktok').
             Если не указан, процесс обрабатывает все доступные ссылки.
            date (datetime | None): Дата для мониторинга. Если не указана, используется now().
        Returns:
            str: результат выполнения
        """
        if not self.params:
            res = "Couldn't monitor links without parameters"
            logger.error(res)
            return res
        date: datetime = date or timezone.now()
        source_q: Q = Q()
        if source:
            source_q &= Q(source=source)
        # FIXME мб через self сделать? Тогда можно source и date в init передавать, а не в run
        links_to_monitor: QuerySet = MonitoringLink.objects.filter(
            source_q,
            next_monitoring_date__lte=date,
            is_active=True
        )
        if not await links_to_monitor.aexists():
            res = "No links to monitor"
            logger.warning(res)
            return res
        try:
            # TODO refactor
            # if not source or source == 'tiktok':
            #     await self.tiktok_process()
            # if not source or source == 'youtube':
            #     await self.youtube_process()

            await self._monitor_links(links_to_monitor)
            res = "Monitoring successful"
        except Exception as e:
            logger.error(e)
            res = f"Monitor links error: {e}"
        return res

    async def tiktok_process(self):
        """Процесс мониторинга ТТ ссылок"""
        # TODO Нужно разделить процесс обработки ссылок по source
        pass

    async def youtube_process(self):
        """Процесс мониторинга YT ссылок"""
        pass

    @timer
    async def _monitor_links(self, links: QuerySet[MonitoringLink]) -> None:
        """
        Запускает браузер, создает задание для каждой ссылки и сохраняет результаты мониторинга.

        Args:
            links (QuerySet[MonitoringLink]): Набор ссылок для мониторинга.
        """
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=False)  # headless=True чтоб браузер не открывался
            context: BrowserContext = await browser.new_context()
            tasks: list[Task] = [asyncio.create_task(self._process_link(context, link)) async for link in links]
            if tasks:
                results: tuple = await asyncio.gather(*tasks)
                await MonitoringResult.objects.abulk_create(results)
            await browser.close()
        await MonitoringLink.objects.abulk_update(links, fields=["next_monitoring_date"])

    @timer
    async def _process_link(self, context: BrowserContext, link: MonitoringLink) -> MonitoringResult | None:
        """
        Обработчик ссылки: открывает новую страницу в браузере, получает контент со страницы, получает количество
        видео, создает результат мониторинга и обновляет дату следующего мониторинга.

        Args:
            browser (Browser): Инстанс браузера, используемый для загрузки страниц.
            link (MonitoringLink): Объект ссылки, содержащий URL для мониторинга.
        Returns:
            MonitoringResult: результат мониторинга ссылки
        """
        page: Page = await context.new_page()
        element: ElementHandle | None = await self._get_page_content(link, page)
        if not element:
            logger.error('No element')
            return None
        video_count_text: str | None = await element.text_content()
        video_count: int = await self._get_video_count(video_count_text)
        result: MonitoringResult = MonitoringResult(
            monitoring_link=link,
            video_count=video_count
        )
        link.next_monitoring_date = timezone.now() + timedelta(hours=self.params.min_monitoring_timeout)
        await page.close()
        return result

    async def _get_page_content(self, link: MonitoringLink, page: Page) -> ElementHandle | None:
        """
        Переходит по URL из link, дожидается загрузки нужного селектора страницы и возвращает его.

        Args:
            link (MonitoringLink): Объект ссылки, содержащий URL.
            page (Page): Объект страницы в браузере, на которой происходит мониторинг.
        Returns:
            ElementHandle: искомый элемент страницы
        """
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

    async def _get_video_count(self, video_count_text) -> int:
        """
        Разбирает строку, представляющую количество видео, возможно содержащую модификаторы масштаба ('K', 'M'), и возвращает целочисленное значение.

        Args:
            video_count_text (str): Текст, содержащий информацию о количестве видео.

        Returns:
            int: количество видео.

        Преобразует строку с аббревиатурой тысяч ('K') и миллионов ('M') в числовое значение.
        """
        match: re.Match | None = re.match(r"(\d+\.?\d*)(K|M)?", video_count_text)
        number: float = float(match.group(1))
        scale: str = match.group(2) or ""
        number *= self.SCALE_MAP.get(scale, 1)
        return int(number)
