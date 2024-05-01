import asyncio
import copy
import csv
import itertools
import logging
import random
import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import TypedDict

import aiohttp
import httpx
import requests
from django.conf import settings

from common.utils import timer, HttpTelegramMessageSender
from scrappers.tiktok.request_params.config import SCRAPPER_TIKTOK_SETTINGS
from scrappers.tiktok.request_params.settings_instances import *  # noqa
from scrappers.tiktok.signature import UserVideoTiktokSignature

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
""".replace("\n", "").replace(" ", "")  # DON'T TOUCH THIS VARIABLE


class CollectedItem(TypedDict):
    link: str
    upload: str
    duration: str
    views: str
    likes: str
    comments: str
    resend: str
    saves: str
    description: str


class TikTokScrapper:
    # ссылка для парсинга музыки
    music_api_url = "https://www.tiktok.com/api/music/item_list/"
    # ссылка для парсинга юзеров
    user_api_url = CONSTANT_USER_API_URL
    # список настроек (из SCRAPPER_TIKTOK_SETTINGS)
    configs = SCRAPPER_TIKTOK_SETTINGS

    def __init__(self):
        self.uniq_ids = set()
        self.total = list()
        self.task_result = "SUCCESS"
        self.user_attempts = settings.TT_USER_ERROR_ATTEMPTS
        self.music_attempts = settings.TT_MUSIC_ERROR_ATTEMPTS

    @timer
    async def run(self, url: str, chat_id: int = None):
        """Основной процесс - точка входа"""
        normalized_data: list[CollectedItem] = []
        report: str = ''
        # парсинг музыки
        if 'music' in url.split('/')[:-1]:
            # вытаскиваем music_id
            music_id = int(url.split('-')[-1].replace('/', ''))
            # курсоры - пагинация. Тут список с шагом в 500
            cursors: list[int] = [i for i in range(0, 5001, 500)]
            start_slicer: int = 0
            finish_slicer: int = len(cursors) // len(self.configs)
            async with asyncio.TaskGroup() as task_group:
                # собираем задачи для парсинга
                tasks = []
                for config in self.configs:
                    # перебираем конфиги и берем их них нужные нам элементы
                    headers: dict[str, str] = copy.deepcopy(config.headers)
                    cookies: dict[str, str] = copy.deepcopy(config.cookies)
                    # прокидываем в query параметры music_id
                    params: dict[str, str] = copy.deepcopy(config.params) | {"musicID": music_id, "from_page": "music"}
                    # тут попарно перебираем курсоры и собираем задачи
                    for start_cursor, cursor_breakpoint in zip(
                            cursors[start_slicer:finish_slicer], cursors[start_slicer + 1:finish_slicer + 1]
                    ):
                        tasks.append(
                            task_group.create_task(
                                self._request_music_process(headers, cookies, params, start_cursor, cursor_breakpoint)
                            )
                        )
                    start_slicer = finish_slicer
                    finish_slicer += finish_slicer
                    # фикс для последней итерации
                    if finish_slicer > len(cursors):
                        finish_slicer = len(cursors) - 1

            # запускаем процесс парсинга музыки и сохраняем результат
            normalized_data = list(
                itertools.chain.from_iterable(
                    (task.result() for task in tasks if task.done()))
            )
            file_name = f'music_report.csv'
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
            file_name = f'user_report.csv'
        report += (
            f'Отчет по {url} \n'
            f'Собрано {len(self.uniq_ids)} уникальных видео'
            f'\nВсего собрано {len(self.total)} видео\n'
        )
        logger.info(report)
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
            report = (
                f'Отчет по id: {normalized_data[0].get("link").split("video")[0]} \n'
                f'Собрано {len(self.uniq_ids)} уникальных видео'
                f'\nВсего собрано {len(self.total)} видео\n'
            )
        else:
            report = (
                f'Отчет по id: {sec_uid} \n'
                f'Собрано {len(self.uniq_ids)} уникальных видео'
                f'\nВсего собрано {len(self.total)} видео\n'
            )
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
            serialized_data = await self._scrape_user_page(sec_uid, cursor) or {}
            for item in serialized_data.get('itemList', []):
                if collected := self._parse_collected_from_json(item):
                    collected_items.append(collected)

            if not serialized_data.get('hasMore'):
                attempt += 1
                logger.debug(f'Limit: {cursor}')
                await asyncio.sleep(random.randint(1, 5))
                continue

            cursor = serialized_data.get('cursor')
        return collected_items

    async def _scrape_user_page(self, sec_uid: str, cursor: int) -> CollectedItem | None:
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
            self.task_result = "With an error"
            return None

        try:
            serialized_data = response.json()
        except JSONDecodeError:
            logger.debug(f'No content:\n{response.text}')
            return None
        return serialized_data

    async def _request_music_process(
            self,
            headers: dict[str, str],
            cookies: dict[str, str],
            params: dict[str: str],
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
                params |= {"cursor": cursor}

                serialized_data = (
                        await self._async_get_request(session, self.music_api_url, headers, cookies, params) or {}
                )
                for item in serialized_data.get('itemList', []):
                    if collected := self._parse_collected_from_json(item):
                        collected_items.append(collected)

                if not serialized_data.get('hasMore'):
                    logger.debug(f'Limit: {cursor}')
                    attempt += 1
                    continue
                cursor = int(serialized_data.get('cursor'))
        return collected_items

    async def _async_get_request(self, session, url, headers, cookies, params) -> dict | None:
        """Метод для отправки асинхронного гет запроса (с вложенной логикой обновления токенов и отлова ошибок"""
        try:
            async with session.get(url, headers=headers, cookies=cookies, params=params) as response:
                response.raise_for_status()
                if (new_ms_token := response.cookies.get('msToken')):
                    cookies |= {"msToken": new_ms_token.value}
                    params |= {"msToken": new_ms_token.value}
                return await response.json()
        except Exception as e:
            logger.error(e)
            self.task_result = "With an error"
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
                        logger.error(f"Failed to get page content from {url}. Status code: {response.status_code}")
                        response.raise_for_status()
                    else:
                        content = response.text
            except Exception as e:
                logger.error(e)
                self.task_result = "With an error"
                content = ""
            pattern = r'"secUid":"(.*?)"'
            if match := re.search(pattern, content):
                sec_uid = match.group(1)
                # тут был кейс, когда отправляли запросы, а вместо нормального id пользователя возвращался id @tiktok
                if sec_uid != 'MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM':  # ignored @tiktok sec uid
                    return sec_uid
            attempt += 1
            await asyncio.sleep(2)

        if not sec_uid:
            logger.error(f"Failed to find secUid on the page from url {url}.")
        return None

    def _parse_collected_from_json(self, json_item: dict) -> CollectedItem | None:
        """Вытаскивает из полученного json объекта информацию о видео"""
        author_id: str = json_item.get('author', {}).get('uniqueId')
        video_id: str = json_item.get('id')
        stats: dict = json_item.get('stats')

        if not author_id or not stats or not video_id:
            logger.info(f'No content from item:\n{json_item}')
            return None
        self.total.append(f'{author_id}@{video_id}')

        if f"{author_id}@{video_id}" in self.uniq_ids:
            logger.info(f'Duplicated item: {author_id}@{video_id}')
            return None
        self.uniq_ids.add(f"{author_id}@{video_id}")
        return CollectedItem(
            link=f"https://www.tiktok.com/@{author_id}/video/{video_id}",
            upload=self._format_timestamp(json_item.get('createTime', '-')),
            duration=json_item.get('video', {}).get('duration', '-'),
            views=stats.get('playCount', '-'),
            likes=stats.get('diggCount', '-'),
            comments=stats.get('commentCount', '-'),
            resend=stats.get('shareCount', '-'),
            saves=stats.get('collectCount', '-'),
            description=json_item.get('desc'),
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
