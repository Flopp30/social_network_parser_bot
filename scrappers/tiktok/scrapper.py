import asyncio
import copy
import csv
import itertools
import logging
import random
import re
from asyncio import Task
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import TypedDict, Any

import aiohttp
import httpx
import requests
from TikTokApi.exceptions import InvalidResponseException
from django.conf import settings
from TikTokApi import TikTokApi
from more_itertools import chunked

from common.utils import HttpTelegramMessageSender, timer
from scrappers.tiktok.request_params.config import SCRAPPER_TIKTOK_SETTINGS
from scrappers.tiktok.request_params.settings_instances import *  # noqa
from scrappers.tiktok.signature import UserVideoTiktokSignature
from scrappers.youtube.request_params.params import TypeHeaders, TypeCookies, TypeParams

logger = logging.getLogger('tiktok_scrapper')

CONSTANT_USER_API_URL = """
     https://www.tiktok.com/api/post/item_list/
     ?aid=1988&app_language=en
     &app_name=tiktok_web
     &battery_info=1
     &browser_language=en-US&
     browser_name=Mozilla
     &browser_online=true
     &browser_platform=Win32
     &browser_version=5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F107.0.0.0%20Safari%2F537.36%20Edg%2F107.0.1418.56
     &channel=tiktok_web
     &cookie_enabled=true
     &device_id=7165118680723998214
     &device_platform=web_pc
     &focus_state=true
     &from_page=user
     &history_len=3
     &is_fullscreen=false
     &is_page_visible=true
     &os=windows
     &priority_region=RO
     &referer=
     &region=RO
     &screen_height=1440
     &screen_width=2560
     &tz_name=Europe%2FBucharest
     &webcast_language=en
     &msToken=G3C-3f8JVeDj9OTvvxfaJ_NppXWzVflwP1dOclpUOmAv4WmejB8kFwndJufXBBrXbeWNqzJgL8iF5zn33da-ZlDihRoWRjh_TDSuAgqSGAu1-4u2YlvCATAM2jl2J1dwNPf0_fk9dx1gJxQ21S0=
     &X-Bogus=DFSzswVYxTUANS/JS8OTqsXyYJUo
     &_signature=_02B4Z6wo00001CoOkNwAAIDBCa--cQz5e0wqDpRAAGoE8f
""".replace('\n', '').replace(' ', '')  # DON'T TOUCH THIS VARIABLE


class SimpleCollectedItem(TypedDict):
    country_code: str
    views: str
    likes: str
    comments: str
    resend: str
    saves: str


class CollectedItem(TypedDict):
    link: str
    views: str
    likes: str
    comments: str
    resend: str
    saves: str
    upload: str
    duration: str
    description: str
    country_code: str | None


class TikTokScrapper:
    # TODO убрать self.task_result (перевести на исключения и отлавливать их)
    # ссылка для парсинга музыки
    music_api_url = 'https://www.tiktok.com/api/music/item_list/'
    # ссылка для парсинга юзеров
    user_api_url = CONSTANT_USER_API_URL
    # список настроек (из SCRAPPER_TIKTOK_SETTINGS)
    configs = SCRAPPER_TIKTOK_SETTINGS

    def __init__(self):
        self.uniq_ids = set()
        self.total = list()
        self.task_result = 'SUCCESS'
        self.user_attempts = settings.TT_USER_ERROR_ATTEMPTS
        self.music_attempts = settings.TT_MUSIC_ERROR_ATTEMPTS

        # TikTokApi
        self.tiktok_api_ms_tokens = settings.TIKTOK_MS_TOKEN

    @timer(print_logger=False)
    async def run(self, url: str, chat_id: int = None, with_geo: bool = False):
        try:
            return await self._process(url, chat_id, with_geo)
        except Exception as e:
            error_msg = f'{type(e).__name__}: {e}'
            logger.error(error_msg)
            return error_msg

    async def _process(self, url: str, chat_id: int = None, with_geo: bool = False):
        """Основной процесс - точка входа"""
        normalized_data: list[CollectedItem] = []
        report: str = ''
        # парсинг музыки
        if 'music' in url.split('/')[:-1]:
            # вытаскиваем music_id
            music_id: int = int(url.split('-')[-1].replace('/', ''))
            # курсоры - пагинация. Тут список с шагом в 500
            cursors: list[int] = [i for i in range(0, 5001, 500)]
            start_slicer: int = 0
            finish_slicer: int = len(cursors) // len(self.configs)
            async with asyncio.TaskGroup() as task_group:
                # собираем задачи для парсинга
                tasks = []
                for config in self.configs:
                    # перебираем конфиги и берем их них нужные нам элементы
                    headers: TypeHeaders = copy.deepcopy(config.headers)
                    cookies: TypeCookies = copy.deepcopy(config.cookies)
                    # прокидываем в query параметры music_id
                    params: TypeParams = copy.deepcopy(config.params) | {'musicID': music_id, 'from_page': 'music'}
                    # тут попарно перебираем курсоры и собираем задачи
                    for start_cursor, cursor_breakpoint in zip(
                        cursors[start_slicer:finish_slicer],
                        cursors[start_slicer + 1 : finish_slicer + 1],
                    ):
                        tasks.append(
                            task_group.create_task(
                                self._request_music_process(headers, cookies, params, start_cursor, cursor_breakpoint),
                            ),
                        )
                    start_slicer = finish_slicer
                    finish_slicer += finish_slicer
                    # фикс для последней итерации
                    if finish_slicer > len(cursors):
                        finish_slicer = len(cursors) - 1

            # запускаем процесс парсинга музыки и сохраняем результат
            normalized_data = list(
                itertools.chain.from_iterable(task.result() for task in tasks if task.done()),
            )
            file_name = 'music_report.csv'
        else:
            # процесс парсинга аккаунта (страницы пользователя)
            # т.к. требует подписания сигнатуры, асинхронно собирать не получается (помню, что была какая-то проблема, но не помню почему)

            # получаем уникальный идентификатор пользователя (просто запросом со страницы
            sec_uid: str | None = await self._get_sec_uid_from_url(url)
            if sec_uid:
                # если он есть - запускаем процесс парсинга
                normalized_data = await self._request_user_process(sec_uid)
            else:
                report += (
                    'Не смог получить уникальный идентификатор пользователя со страницы.'
                    '\nИмеет смысл повторить запрос или через какое-то время попробовать снова\n\n'
                )
            file_name = 'user_report.csv'
        report += f'Отчет по {url} \n' f'Собрано {len(self.uniq_ids)} уникальных видео' f'\nВсего собрано {len(self.total)} видео\n'
        logger.info(report)

        # если требуется добавить гео: все собранные видео повторно прогоняем через TikTokApi, чтобы получить country code
        if with_geo and normalized_data:
            normalized_data = await self._add_geo_to_collected_items(normalized_data)

        # если передан tg chat id, то отправляем в стриме
        if chat_id:
            return await HttpTelegramMessageSender.send_csv_doc(chat_id, normalized_data, report, file_name)

        # иначе сохраняем в csv (используется для ручного тестирования в основном)
        self._save_to_csv(collected=normalized_data, filename=file_name)
        return self.task_result

    async def run_by_user_uuid(self, sec_uid, chat_id=None):
        """Метод, который выполняет полный цикл парсинга аккаунта (вызывается отдельно, не через run)"""
        # NOTE по сути был добавлен, потому что в какой-то момент парсили видео по sec uid (а не через ссылку, как сейчас)
        normalized_data = await self._request_user_process(sec_uid)
        if normalized_data:
            if len(normalized_data) > 0 and 'link' in normalized_data[0] and normalized_data[0]['link'] is not None:
                link = normalized_data[0].get('link').split('video')[0]  # type: ignore
            else:
                link = ''
            report = f'Отчет по id: {link} \n' f'Собрано {len(self.uniq_ids)} уникальных видео' f'\nВсего собрано {len(self.total)} видео\n'
        else:
            report = f'Отчет по id: {sec_uid} \n' f'Собрано {len(self.uniq_ids)} уникальных видео' f'\nВсего собрано {len(self.total)} видео\n'
        file_name = 'user_report.csv'
        logger.info(report)
        if chat_id:
            return await HttpTelegramMessageSender.send_csv_doc(chat_id, normalized_data, report, file_name)

        self._save_to_csv(collected=normalized_data, filename=file_name)
        return self.task_result

    async def _request_user_process(self, sec_uid) -> list[CollectedItem]:
        """Парсит страницу пользователя (по sec_uid) и возвращает список собранных данных"""
        collected_items: list[CollectedItem] = []
        cursor = 0
        attempt = 0
        while attempt < self.user_attempts:
            serialized_data: dict | None = await self._scrape_user_page(sec_uid, cursor) or {}
            if not serialized_data:
                attempt += 1
                logger.debug(f'Limit: {cursor}')
                await asyncio.sleep(random.randint(1, 5))
                continue

            for item in serialized_data.get('itemList', []):
                if collected := self._parse_collected_from_json(item):
                    collected_items.append(collected)

            if not serialized_data.get('hasMore'):
                attempt += 1
                logger.debug(f'Limit: {cursor}')
                await asyncio.sleep(random.randint(1, 5))
                continue

            try:
                cursor = int(serialized_data.get('cursor', 0))
            except ValueError:
                attempt += 1

        return collected_items

    async def _scrape_user_page(self, sec_uid: str, cursor: int) -> dict[str, Any] | None:
        logger.debug(f'Parse. Cursor: {cursor}')
        headers: dict[str, str] | None = await UserVideoTiktokSignature.get_request_headers(sec_uid, cursor)
        if headers is None:
            logger.error('Error in the response from the internal service (signer)')
            return None
        try:
            # отправляется обычный медленный get запроса, потому что в любой другой конфигурации возвращается пустой ответ :(
            response = requests.get(CONSTANT_USER_API_URL, headers=headers)
            response.raise_for_status()
        except Exception as e:
            logger.error(e)
            self.task_result = f'{type(e).__name__} {e}'
            return None

        try:
            serialized_data = response.json()
        except JSONDecodeError:
            logger.debug(f'No content:\n{response.text}')
            return None
        return serialized_data

    async def _request_music_process(
        self,
        headers: TypeHeaders,
        cookies: TypeCookies,
        params: TypeParams,
        start_cursor: int,
        cursor_breakpoint: int,
    ) -> list[CollectedItem]:
        """Метод парсинга музыки. Принимает курсор и возвращает список собранных данных"""
        collected_items = []
        cursor = start_cursor
        attempt = 0
        async with aiohttp.ClientSession() as session:
            while cursor < cursor_breakpoint and attempt < self.music_attempts:
                await asyncio.sleep(random.randint(1, 3))
                logger.debug(f'Parse. Start: {cursor}; Breakpoint: {cursor_breakpoint}')
                params |= {'cursor': cursor}

                serialized_data = await self._async_get_request(session, self.music_api_url, headers, cookies, params) or {}
                for item in serialized_data.get('itemList', []):
                    if collected := self._parse_collected_from_json(item):
                        collected_items.append(collected)

                if not serialized_data.get('hasMore'):
                    logger.debug(f'Limit: {cursor}')
                    attempt += 1
                    continue

                try:
                    cursor = int(serialized_data.get('cursor'))  # type: ignore
                except ValueError:
                    attempt += 1

        return collected_items

    async def _async_get_request(self, session, url, headers, cookies, params) -> dict | None:
        """Метод для отправки асинхронного гет запроса (с вложенной логикой обновления токенов и отлова ошибок"""
        try:
            async with session.get(url, headers=headers, cookies=cookies, params=params) as response:
                response.raise_for_status()
                if new_ms_token := response.cookies.get('msToken'):
                    cookies |= {'msToken': new_ms_token.value}
                    params |= {'msToken': new_ms_token.value}
                return await response.json()
        except Exception as e:
            logger.error(e)
            self.task_result = f'{type(e).__name__} {e}'
            return None

    async def _get_sec_uid_from_url(self, url: str) -> str | None:
        """Пытается получить уникальный идентификатор пользователя со страницы"""
        sec_uid = None
        attempt = 0
        while not sec_uid or attempt < 5:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    if response.status_code != 200:
                        logger.error(f'Failed to get page content from {url}. Status code: {response.status_code}')
                        response.raise_for_status()
                    else:
                        content = response.text
            except Exception as e:
                logger.error(e)
                self.task_result = f'{type(e).__name__} {e}'
                content = ''
            pattern = r'"secUid":"(.*?)"'
            if match := re.search(pattern, content):
                sec_uid = match.group(1)
                # тут был кейс, когда отправляли запросы, а вместо нормального id пользователя возвращался id @tiktok
                if sec_uid != 'MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM':  # ignored @tiktok sec uid
                    return sec_uid
            attempt += 1
            await asyncio.sleep(2)

        if not sec_uid:
            logger.error(f'Failed to find secUid on the page from url {url}.')
        return None

    def _parse_collected_from_json(self, json_item: dict) -> CollectedItem | None:
        """Вытаскивает из полученного json объекта информацию о видео"""
        author_id: str = json_item.get('author', {}).get('uniqueId')
        video_id: str | None = json_item.get('id')
        stats: dict | None = json_item.get('stats')

        if not author_id or not stats or not video_id:
            logger.info(f'No content from item:\n{json_item}')
            return None
        self.total.append(f'{author_id}@{video_id}')

        if f'{author_id}@{video_id}' in self.uniq_ids:
            logger.info(f'Duplicated item: {author_id}@{video_id}')
            return None
        self.uniq_ids.add(f'{author_id}@{video_id}')
        return CollectedItem(
            link=f'https://www.tiktok.com/@{author_id}/video/{video_id}',
            upload=self._format_timestamp(json_item.get('createTime', '-')),
            duration=json_item.get('video', {}).get('duration', '-'),
            views=stats.get('playCount', '-'),
            likes=stats.get('diggCount', '-'),
            comments=stats.get('commentCount', '-'),
            resend=stats.get('shareCount', '-'),
            saves=stats.get('collectCount', '-'),
            description=json_item.get('desc', ''),
            country_code=None,
        )

    @staticmethod
    def _save_to_csv(collected: list[CollectedItem], filename: str = 'report.csv'):
        """Сохраняет в csv файл"""
        file_path = Path(__file__).resolve().parent / filename
        fieldnames = ['link', 'upload', 'duration', 'views', 'likes', 'comments', 'resend', 'saves', 'description']
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(collected)  # type:ignore

    @staticmethod
    def _format_timestamp(timestamp) -> str:
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return '-'

    async def get_one_video_stat(self, chat_id: int, url: str) -> str:
        """Получает статистику по одной ссылке"""
        try:
            async with TikTokApi() as api:
                await api.create_sessions(
                    ms_tokens=self.tiktok_api_ms_tokens,
                    num_sessions=1,
                    sleep_after=1,
                    executable_path='/opt/google/chrome/google-chrome',
                    override_browser_args=['--mute-audio'],
                    cookies=[config.cookies for config in self.configs],
                )
                video_stat: SimpleCollectedItem = await self._get_video_stat(url, api)
        except Exception as e:
            logger.error(e)
            return f'{type(e).__name__}: {e}'

        text_message: str = (
            f'Ссылка: {url}\n'
            f'Страна загрузка: {video_stat["country_code"]}\n'
            f'Просмотры: {video_stat["views"]}\n'
            f'Лайки: {video_stat["likes"]}\n'
            f'Комменты: {video_stat["comments"]}\n'
            f'Репосты: {video_stat["resend"]}\n'
            f'Сохранения: {video_stat["saves"]}\n'
        )
        return await HttpTelegramMessageSender.send_text_message(chat_id, text_message)

    async def _get_video_stat(self, url: str, api_connector: TikTokApi) -> SimpleCollectedItem:
        video = api_connector.video(url=url)
        video_info = await video.info()
        video_stat = video_info.get('stats')
        return SimpleCollectedItem(
            country_code=video_info.get('locationCreated'),
            views=video_stat.get('playCount', '-'),
            likes=video_stat.get('diggCount', '-'),
            comments=video_stat.get('commentCount', '-'),
            resend=video_stat.get('shareCount', '-'),
            saves=video_stat.get('collectCount', '-'),
        )

    async def _add_geo_to_item(self, item: CollectedItem, api_connector: TikTokApi):
        video = api_connector.video(url=item['link'])
        attempt_count = 3

        while item['country_code'] is None and attempt_count > 0:
            try:
                video_info = await video.info()
                item['country_code'] = video_info.get('locationCreated')
            except InvalidResponseException as e:
                logger.error(f'{type(e).__name__}: {e}')
                attempt_count -= 1
            except Exception as e:
                logger.error(f'{type(e).__name__}: {e}')
                break

    async def _add_geo_to_collected_items(self, collected_items: list[CollectedItem]) -> list[CollectedItem]:
        """Собирает гео для уже полученных данных"""
        # все обложено try:except, т.к. это не килл-фича и в целом главное вернуть результат, даже если там не будет гео
        tasks: list[Task] = []
        chunk_size: int = 10
        sleep_time: float = 0.5
        try:
            async with TikTokApi() as api:
                await api.create_sessions(
                    ms_tokens=self.tiktok_api_ms_tokens,
                    num_sessions=chunk_size,
                    sleep_after=1,
                    executable_path='/opt/google/chrome/google-chrome',
                    cookies=[config.cookies for config in self.configs],
                    override_browser_args=['--mute-audio'],
                )
                for item in collected_items:
                    tasks.append(
                        asyncio.create_task(
                            self._add_geo_to_item(item, api),
                        )
                    )
                for chunk in chunked(tasks, chunk_size):
                    await asyncio.gather(*chunk)
                    await asyncio.sleep(sleep_time)
        except Exception as e:
            logger.error(f'{type(e).__name__}: {e}')
        return collected_items
