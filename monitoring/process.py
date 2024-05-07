import asyncio
import logging
import re
from asyncio import Task
from datetime import datetime, timedelta

import httpx
from django.db.models import QuerySet, Q
from django.utils import timezone
from playwright.async_api import async_playwright, Browser, Page, ElementHandle, BrowserContext
from setuptools._vendor.more_itertools.more import chunked

from common.utils import timer
from monitoring.models import MonitoringLink, MonitoringResult, Parameter
from monitoring.parsers import YtMusicVideoCountParser, YtUserVideoCountParser

logger = logging.getLogger('monitoring')


class LinkMonitoringProcess:
    def __init__(self, source: MonitoringLink.Sources | None = None, date: datetime | None = None):
        """
        Инициализация процесса мониторинга

        Args:
            source (str | None): Источник ссылок для мониторинга ('youtube', 'tiktok', или None).
            date (datetime | None): Дата для мониторинга.
        """
        self.params: Parameter = Parameter.objects.first()
        self.date: datetime = date or timezone.now()
        self.source: str = source

    async def run(self):
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
            res = 'No parameters'
            logger.error(res)
            return res
        try:

            if not self.source or self.source == MonitoringLink.Sources.TIKTOK:
                tt_process: TtMonitoringProcess = TtMonitoringProcess(self.params, self.date)
                await tt_process.run()
            if not self.source or self.source == MonitoringLink.Sources.YOUTUBE:
                yt_process: YtMonitoringProcess = YtMonitoringProcess(self.params, self.date)
                await yt_process.run()

            res = "Monitoring successful"
        except Exception as e:
            logger.error(e)
            res = f"Monitor links error: {e}"
        return res


class YtMonitoringProcess:
    music_parser: YtMusicVideoCountParser = YtMusicVideoCountParser
    profile_parser: YtUserVideoCountParser = YtUserVideoCountParser
    REQUEST_USER_ATTEMPTS: int = 3

    def __init__(self, param: Parameter | None = None, date: datetime | None = None, links: QuerySet[MonitoringLink] | None = None):
        self.params: Parameter = param or Parameter.objects.first()
        self.date = date if date else datetime.now()
        self.links = links if links else MonitoringLink.objects.filter(
            is_active=True,
            next_monitoring_date__gte=self.date,
            source=MonitoringLink.Sources.YOUTUBE
        )

    @timer
    async def run(self):
        if not await self.links.aexists():
            return
        async with httpx.AsyncClient() as client:
            profile_tasks: list[Task] = []
            music_tasks: list[Task] = []
            async for link in self.links[:self.params.max_link_per_process_count]:
                if link.source != MonitoringLink.Sources.YOUTUBE:
                    continue

                if '/source/' in link.url:
                    music_tasks.append(asyncio.create_task(self.get_yt_music_video_count(link, client, self.music_parser)))
                else:
                    profile_tasks.append(asyncio.create_task(self.get_yt_user_video_count(link, client, self.profile_parser)))

            if profile_tasks:
                logger.debug('Found {} profile links'.format(len(profile_tasks)))
                for chunk in chunked(profile_tasks, self.params.max_link_per_run_count):
                    results: tuple = await asyncio.gather(*chunk)
                    await MonitoringResult.objects.abulk_create(results)
                    await asyncio.sleep(self.params.monitoring_iteration_timeout_seconds)

            if music_tasks:
                logger.debug('Found {} music links'.format(len(music_tasks)))
                for chunk in chunked(music_tasks, self.params.max_link_per_run_count):
                    results: tuple = await asyncio.gather(*chunk)
                    await MonitoringResult.objects.abulk_create(results)
                    await asyncio.sleep(self.params.monitoring_iteration_timeout_seconds)

        await MonitoringLink.objects.abulk_update(self.links, fields=["next_monitoring_date"])

    @timer
    async def get_yt_user_video_count(self, link: MonitoringLink, client: httpx.AsyncClient, parser: YtUserVideoCountParser) -> MonitoringResult | None:
        """Возвращает количество суммарное количество видео для одного ютуб профиля"""
        attempt: int = 0
        resp: httpx.Response | None = None
        while attempt < self.REQUEST_USER_ATTEMPTS:
            try:
                resp: httpx.Response = await client.get(link.url)
                resp.raise_for_status()
            except Exception as e:
                logger.error(f"An unexpected error occurred on attempt {attempt + 1} for URL {link.url}: {e}")
            html_content: str = resp.text
            video_count: int | None = await parser.get_video_count(html_content)
            logger.debug(f'{link.url} - {video_count}')
            if video_count:
                result: MonitoringResult = MonitoringResult(
                    monitoring_link=link,
                    video_count=video_count
                )
                link.next_monitoring_date = timezone.now() + timedelta(hours=self.params.min_monitoring_timeout)
                return result
            else:
                logger.error(f"Failed to parse video count on attempt {attempt + 1} for URL {link.url}")
            attempt += 1
        return None

    @timer
    async def get_yt_music_video_count(self, link: MonitoringLink, client: httpx.AsyncClient, parser: YtMusicVideoCountParser) -> MonitoringResult | None:
        """Возвращает суммарное количество коротких видео для одного ютуб звука"""
        try:
            resp: httpx.Response = await client.get(link.url)
            resp.raise_for_status()
        except Exception as e:
            logger.error(e)
            return None
        html_content: str = resp.text
        video_count: int | None = await parser.get_video_count(html_content)
        result: MonitoringResult = MonitoringResult(
            monitoring_link=link,
            video_count=video_count
        )
        link.next_monitoring_date = timezone.now() + timedelta(hours=self.params.min_monitoring_timeout)
        logger.debug(f'{link.url} - {video_count}')
        return result


class TtMonitoringProcess:
    TIMEOUT_MILLISECONDS: int = 100000
    TIMEOUT_ATTEMPTS: int = 3
    SCALE_MAP: dict = {
        'K': 1000,
        'M': 1000_000,
    }

    def __init__(self, param: Parameter | None = None, date: datetime | None = None, links: QuerySet[MonitoringLink] | None = None):
        self.params: Parameter = param or Parameter.objects.first()
        self.date = date if date else datetime.now()
        self.links: QuerySet[MonitoringLink] = links if links else MonitoringLink.objects.filter(
            is_active=True,
            next_monitoring_date__gt=self.date,
            source=MonitoringLink.Sources.TIKTOK
        )

    async def run(self):
        """
        Запускает браузер, создает задание для каждой ссылки тиктока и сохраняет результаты мониторинга.
        """
        if not await self.links.aexists():
            return

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=True)  # headless=True чтоб браузер не открывался
            context: BrowserContext = await browser.new_context()
            tasks: list[Task] = [
                asyncio.create_task(
                    self._process_tt_link(context, link)
                ) async for link in self.links[:self.params.max_link_per_process_count]
            ]
            if tasks:
                logger.info(f'Found {len(tasks)} tt links')
                for chunk in chunked(tasks, self.params.max_link_per_run_count):
                    results: tuple = await asyncio.gather(*chunk)
                    await MonitoringResult.objects.abulk_create(results)
                    await asyncio.sleep(self.params.monitoring_iteration_timeout_seconds)
            await browser.close()
        await MonitoringLink.objects.abulk_update(self.links, fields=["next_monitoring_date"])

    @timer
    async def _process_tt_link(self, context: BrowserContext, link: MonitoringLink) -> MonitoringResult | None:
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
