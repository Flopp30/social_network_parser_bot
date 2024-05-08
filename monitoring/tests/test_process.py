import datetime
import os
from functools import wraps
from typing import Callable
from unittest.mock import patch, AsyncMock

from django.test import TestCase
from django.utils import timezone
from monitoring.models import Parameter, MonitoringLink, MonitoringResult
from monitoring.process import TtMonitoringProcess, YtMonitoringProcess

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def get_page_content(file_name: str):
    with open(os.path.join(DATA_DIR, file_name)) as page_content:
        return page_content.read()


def get_yt_success_user_page_content():
    return get_page_content('success_yt_user_page.html')


def get_yt_error_user_page_content():
    return get_page_content('error_yt_user_page.html')


def get_yt_music_page_content():
    return get_page_content('success_yt_music_page.html')


def patch_httpx(content_callback_func: Callable):
    """Декоратор для мока httpx
    принимает callback функции для получения содержимого страницы
    """
    # NOTE
    # - асинхронный контекстный менеджер возвращает AsyncClient
    # - AsyncClient на метод get возвращает response
    # - response на метод text возвращает текст страницы, который передается в content_callback_func
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with patch('monitoring.process.httpx.AsyncClient') as mocked_httpx:
                client = AsyncMock()
                response = AsyncMock()
                # response text возвращает текст страницы
                response.text = content_callback_func()
                # клиент на метод get возвращает response
                client.get.return_value = response
                # асинхронный контекстный менеджер возвращает клиент
                mocked_httpx.return_value.__aenter__.return_value = client
                res = await func(*args, mocked_httpx, **kwargs)
            return res
        return wrapper
    return decorator


def patch_playwright(video_count: str = '10'):
    """Декоратор для мока playwright"""

    # NOTE для простоты понимания - читать моки снизу вверху (именно так они вызываются в коде)
    # - асинхронный контекстный менеджер возвращает playwright
    # - playwright возвращает браузер
    # - браузер возвращает экземпляр контекста
    # - контекст возвращает вкладку (она же страница)
    # - вкладка возвращает элемент на странице
    # - элемент возвращает количество видео на странице
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):

            with patch('monitoring.process.async_playwright') as mocked_playwright:
                # Создаем отдельные моки для каждого метода
                element = AsyncMock()
                page = AsyncMock()
                context = AsyncMock()
                browser = AsyncMock()
                p = AsyncMock()

                # возвращаем количество видео со страницы через элемент
                element.text_content.return_value = str(video_count)
                # возвращаем элемент со страницы при поиске
                page.wait_for_selector.return_value = element
                # возвращаем объект страницы (вкладки) из контекста браузера
                context.new_page.return_value = page
                # возвращаем объект контекста из браузера
                browser.new_context.return_value = context
                # возвращаем объект браузера из playwright
                p.chromium.launch.return_value = browser
                # асинхронный контекстный менеджер возвращает объект playwright
                mocked_playwright.return_value.__aenter__.return_value = p

                res = await func(*args, mocked_playwright, **kwargs)

            return res
        return wrapper
    return decorator


class TtMonitoringProcessTest(TestCase):
    PROCESS = TtMonitoringProcess
    today = timezone.now()

    def setUp(self):
        self.param = Parameter.objects.create(
            monitoring_iteration_timeout_seconds=0,
        )
        self.tt_link = MonitoringLink.objects.create(
            url='https://tiktok.com',
            source=MonitoringLink.Sources.TIKTOK,
            next_monitoring_date=self.today,
            is_active=True,
        )
        # для проверки, что youtube ссылки не попадают в процессинг по TikTok'у
        self.yt_user_link = MonitoringLink.objects.create(
            url='https://youtube_user.com',
            source=MonitoringLink.Sources.YOUTUBE,
            next_monitoring_date=self.today,
            is_active=True,
        )

        self.yt_music_link = MonitoringLink.objects.create(
            url='https://youtube_music.com/source/',
            source=MonitoringLink.Sources.YOUTUBE,
            next_monitoring_date=self.today,
            is_active=True,
        )

    def tearDown(self):
        MonitoringLink.objects.all().delete()
        MonitoringResult.objects.all().delete()

    @patch_playwright('20')
    async def test_main(self, mocked_playwright: AsyncMock):
        # проверяем, что сохраненных результатов нет
        self.assertEquals(await MonitoringResult.objects.acount(), 0)

        # запускаем процессинг
        await self.PROCESS(param=self.param, date=self.today).run()

        # проверяем, что мок вызывался
        mocked_playwright.assert_called_once()
        mocked_playwright.reset_mock()

        # проверяем, что создали результат мониторинга
        self.assertEqual(await MonitoringResult.objects.acount(), 1)

        # и что он создан именно для tt ссылки
        monitoring_result = await MonitoringResult.objects.afirst()
        self.assertEqual(monitoring_result.monitoring_link_id, self.tt_link.id)

        # количество видео передается в декоратор patch_playwright
        self.assertEqual(monitoring_result.video_count, 20)

        # проверяем, что дата сл мониторинга обновилась согласно параметру
        await self.tt_link.arefresh_from_db()
        self.assertEqual(
            self.tt_link.next_monitoring_date,
            self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout),
        )

        # проверяем, что дата сл мониторинга для yt ссылок не изменилась
        await self.yt_user_link.arefresh_from_db()
        await self.yt_music_link.arefresh_from_db()
        self.assertEquals(
            self.yt_user_link.next_monitoring_date,
            self.yt_music_link.next_monitoring_date,
            self.today,
        )

        # запускам повторно процесс
        new_date = self.today + datetime.timedelta(hours=1)
        await self.PROCESS(param=self.param, date=new_date).run()

        # проверяем, что браузер не открывался
        mocked_playwright.assert_not_called()

        # проверяем, что новых MonitoringResult не создалось, даты мониторинга остались без изменений
        self.assertEqual(await MonitoringResult.objects.acount(), 1)

        # проверяем, что дата сл мониторинга у tt ссылки осталась без изменений
        await self.tt_link.arefresh_from_db()
        self.assertEqual(
            self.tt_link.next_monitoring_date,
            self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout),
        )

        # проверяем, что дата сл мониторинга для yt ссылок не изменилась
        await self.yt_user_link.arefresh_from_db()
        await self.yt_music_link.arefresh_from_db()
        self.assertEquals(
            self.yt_user_link.next_monitoring_date,
            self.yt_music_link.next_monitoring_date,
            self.today,
        )


class YtMonitoringProcessTest(TestCase):
    PROCESS = YtMonitoringProcess
    today = timezone.now()

    def setUp(self):
        self.param = Parameter.objects.create(
            monitoring_iteration_timeout_seconds=0,
        )
        # для проверки, что мы её нигде не изменяем в рамках процесса мониторинга ютуба
        self.tt_link = MonitoringLink.objects.create(
            url='https://tiktok.com',
            source=MonitoringLink.Sources.TIKTOK,
            next_monitoring_date=self.today,
            is_active=True,
        )

    def tearDown(self):
        MonitoringLink.objects.all().delete()
        MonitoringResult.objects.all().delete()

    @patch_httpx(get_yt_success_user_page_content)
    async def test_success_user_page(self, mocked_httpx: AsyncMock):
        # создаем ссылки внутри тестов, т.к. каждый сценарий тестирования из-за мока должен быть разделен (page_content)
        yt_user_link: MonitoringLink = await MonitoringLink.objects.acreate(
            url='https://youtube_user.com',
            source=MonitoringLink.Sources.YOUTUBE,
            next_monitoring_date=self.today,
            is_active=True,
        )
        # проверяем, что нет созданных MonitoringResult
        self.assertEqual(await MonitoringResult.objects.acount(), 0)

        # запускаем процесс
        await self.PROCESS(param=self.param, date=self.today).run()

        # проверяем, что мок вызывался
        mocked_httpx.assert_called_once()
        mocked_httpx.reset_mock()

        # проверяем, что создали MonitoringResult для yt_user_link
        self.assertEqual(await MonitoringResult.objects.acount(), 1)
        monitoring_result = await MonitoringResult.objects.afirst()
        self.assertEqual(monitoring_result.monitoring_link_id, yt_user_link.id)

        # немного хардкода :). Это число берется из сохраненного ответа от ютуба
        self.assertEqual(monitoring_result.video_count, 1800)

        # проверяем, что дата сл мониторинга сдвинута соответственно параметрам
        await yt_user_link.arefresh_from_db()
        self.assertEqual(
            yt_user_link.next_monitoring_date,
            self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout)
        )
        # проверяем, что tt ссылка осталась без изменений
        await self.tt_link.arefresh_from_db()
        self.assertEqual(self.tt_link.next_monitoring_date, self.today)

        # запускаем второй процесс
        new_date = self.today + datetime.timedelta(hours=1)
        await self.PROCESS(param=self.param, date=new_date).run()

        # проверяем, что мок не вызывался
        mocked_httpx.assert_not_called()

        # проверяем, что количество MonitoringResult не изменилось
        self.assertEqual(await MonitoringResult.objects.acount(), 1)

        # проверяем, что next_monitoring_date остался без изменений у обоих ссылок
        await yt_user_link.arefresh_from_db()
        self.assertEqual(
            yt_user_link.next_monitoring_date,
            self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout)
        )

        # проверяем, что tt ссылка осталась без изменений
        await self.tt_link.arefresh_from_db()
        self.assertEqual(self.tt_link.next_monitoring_date, self.today)

    @patch_httpx(get_yt_error_user_page_content)
    async def test_error_user_page(self, mocked_httpx: AsyncMock):
        yt_user_link: MonitoringLink = await MonitoringLink.objects.acreate(
            url='https://youtube_user.com',
            source=MonitoringLink.Sources.YOUTUBE,
            next_monitoring_date=self.today,
            is_active=True,
        )
        # проверяем, что нет созданных MonitoringResult
        self.assertEqual(await MonitoringResult.objects.acount(), 0)

        # запускаем процесс
        await self.PROCESS(param=self.param, date=self.today).run()

        # проверяем, что мок вызывался
        mocked_httpx.assert_called_once()

        # Проверяем, что результатов мониторинга не создано (т.к. ответ не удалось получить)
        self.assertEqual(await MonitoringResult.objects.acount(), 0)

        # проверяем, что дата сл мониторинга не изменилась
        await yt_user_link.arefresh_from_db()
        self.assertEqual(yt_user_link.next_monitoring_date, self.today)

    @patch_httpx(get_yt_music_page_content)
    async def test_success_music_page(self, mocked_httpx: AsyncMock):
        yt_music_link = await MonitoringLink.objects.acreate(
            url='https://youtube_music.com/source/',
            source=MonitoringLink.Sources.YOUTUBE,
            next_monitoring_date=self.today,
            is_active=True,
        )
        # проверяем, что нет созданных MonitoringResult
        self.assertEqual(await MonitoringResult.objects.acount(), 0)

        # запускаем процесс
        await self.PROCESS(param=self.param, date=self.today).run()

        # проверяем, что мок вызывался
        mocked_httpx.assert_called_once()
        mocked_httpx.reset_mock()

        # Проверяем, что создали MonitoringResult для yt_music_link
        self.assertEqual(await MonitoringResult.objects.acount(), 1)
        monitoring_result = await MonitoringResult.objects.afirst()
        self.assertEqual(monitoring_result.monitoring_link_id, yt_music_link.id)

        # количество зашито в ответе от youtube (см. test/data/yt_music_page_content.html)
        self.assertEqual(monitoring_result.video_count, 6)

        # проверяем, что дата сл мониторинга обновилась согласно параметру
        await yt_music_link.arefresh_from_db()
        self.assertEqual(yt_music_link.next_monitoring_date, self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout))
        await self.tt_link.arefresh_from_db()
        self.assertEqual(self.tt_link.next_monitoring_date, self.today)

        # запускам процессинг еще раз
        new_date = self.today + datetime.timedelta(hours=1)
        await self.PROCESS(param=self.param, date=new_date).run()

        # проверяем, что мок не вызывался
        mocked_httpx.assert_not_called()

        # проверяем, что количество MonitoringResult не изменилось
        self.assertEqual(await MonitoringResult.objects.acount(), 1)

        # проверяем, что next_monitoring_date остались без изменений
        await yt_music_link.arefresh_from_db()
        self.assertEqual(yt_music_link.next_monitoring_date, self.today + datetime.timedelta(hours=self.param.min_monitoring_timeout))
        await self.tt_link.arefresh_from_db()
        self.assertEqual(self.tt_link.next_monitoring_date, self.today)