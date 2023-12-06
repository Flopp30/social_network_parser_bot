import asyncio
import copy
import csv
import io
import itertools
import logging
import random
import re
import time
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from urllib.parse import urlencode

import aiohttp
import httpx
import requests
from django.conf import settings
from scrappers.tiktok.request_params.models import SCRAPPER_TIKTOK_SETTINGS
from scrappers.tiktok.request_params.settings_instances import *

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

CollectedItem = dict[str:str]

try:
    TT_SIGNATURE_URL = settings.TT_SIGNATURE_URL
except Exception:
    TT_SIGNATURE_URL = 'http://localhost:8080/signature'


def timer(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f'Время выполнения функции {func.__name__}: {execution_time} сек')
        return result

    return wrapper


class TikTokScrapper:
    music_api_url = "https://www.tiktok.com/api/music/item_list/"
    user_signature_url = TT_SIGNATURE_URL
    user_fake_api_url = "https://m.tiktok.com/api/post/item_list/?"
    user_api_url = CONSTANT_USER_API_URL
    configs = SCRAPPER_TIKTOK_SETTINGS
    try:
        tg_api_send_doc_url = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendDocument"
    except Exception:
        tg_api_send_doc_url = ''

    def __init__(self):
        self.uniq_ids = set()
        self.total = list()
        self.task_result = "SUCCESS"
        try:
            self.user_attempts = settings.TT_USER_ERROR_ATTEMPTS
            self.music_attempts = settings.TT_MUSIC_ERROR_ATTEMPTS
        except Exception:
            self.user_attempts = 5
            self.music_attempts = 3

    @timer
    async def run(self, url: str, tg_chat_id: int = None):
        normalized_data = []
        report = ''
        if 'music' in url.split('/')[:-1]:
            music_id = int(url.split('-')[-1].replace('/', ''))
            cursors = [i for i in range(0, 5001, 500)]
            start_slicer = 0
            finish_slicer = len(cursors) // len(self.configs)
            async with asyncio.TaskGroup() as task_group:
                tasks = []
                for config in self.configs:
                    headers = copy.deepcopy(config.headers)
                    cookies = copy.deepcopy(config.cookies)
                    params = copy.deepcopy(config.params) | {"musicID": music_id, "from_page": "music"}
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
                    if finish_slicer > len(cursors):
                        finish_slicer = len(cursors) - 1
            normalized_data = list(
                itertools.chain.from_iterable(
                    (task.result() for task in tasks if task.done()))
            )
            file_name = f'music_report.csv'
        else:
            sec_uid = await self._get_sec_uid_from_url(url)
            if sec_uid:
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
        if tg_chat_id:
            await self._send_report_to_tg(tg_chat_id, normalized_data, file_name, report)
            return self.task_result
        self._save_to_csv(collected=normalized_data, filename=file_name)
        return self.task_result

    async def run_by_user_uuid(self, sec_uid, tg_chat_id=None):
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
        if tg_chat_id:
            await self._send_report_to_tg(tg_chat_id, normalized_data, file_name, report)
            return self.task_result
        self._save_to_csv(collected=normalized_data, filename=file_name)
        return self.task_result

    async def _send_report_to_tg(
            self,
            tg_chat_id,
            normalized_data: list[CollectedItem],
            file_name: str = 'report.csv',
            report: str = ''
    ):
        string_io = self.get_string_io(normalized_data)
        csv_data = string_io.getvalue().encode('utf-8')
        files = {
            "document": (file_name, csv_data, "text/csv"),
        }
        params = {
            "chat_id": tg_chat_id,
            "caption": report
        }
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.tg_api_send_doc_url, params=params, files=files)
                response.raise_for_status()
                logger.info(f"Report send with status {response.status_code}")
        except Exception as e:
            logger.error(response.__dict__)
            logger.error(e)
            self.task_result = "With an error"

    async def _request_user_process(self, sec_uid) -> list[CollectedItem]:
        collected_items = []
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
        params = {
            "aid": "1988",
            "count": 30,
            "cookie_enabled": "true",
            "screen_width": 0,
            "screen_height": 0,
            "browser_language": "",
            "browser_platform": "",
            "browser_name": "",
            "browser_version": "",
            "browser_online": "",
            "timezone_name": "Europe/London",
            "secUid": sec_uid,
            "cursor": cursor
        }
        fake_user_url = self.user_fake_api_url + urlencode(params)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    self.user_signature_url,
                    headers={'Content-type': 'application/json'},
                    data=fake_user_url
            ) as response:
                try:
                    serialized_data = await response.json()
                except JSONDecodeError:
                    logger.error('Error in the response from the internal service (signer)')
                    self.task_result = "With an error"
                    return None

        if not (tt_params := serialized_data.get('data', {}).get('x-tt-params')):
            logger.warning(f'tt_params not found in {serialized_data}')
            self.task_result = "With an error"
            return None
        headers = {
            "x-tt-params": tt_params,
            'user-agent': (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56"
            ),
        }
        try:
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
            headers: dict[str:str],
            cookies: dict[str:str],
            params: dict[str: str],
            start_cursor: int,
            cursor_breakpoint: int,
    ) -> list[CollectedItem]:
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
        sec_uid = None
        attempt = 0
        while not sec_uid or attempt < 5:
            attempt += 1
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
            if (match := re.search(pattern, content)):
                sec_uid = match.group(1)
                if sec_uid != 'MS4wLjABAAAAv7iSuuXDJGDvJkmH_vz1qkDZYo1apxgzaxdBSeIuPiM':  # @tiktok sec uid
                    return sec_uid
            await asyncio.sleep(2)

        if not sec_uid:
            logger.error(f"Failed to find secUid on the page from url {url}.")
        return None

    def _parse_collected_from_json(self, json_item: dict) -> CollectedItem | None:
        author_id = json_item.get('author', {}).get('uniqueId')
        video_id = json_item.get('id')
        stats = json_item.get('stats')
        if not author_id or not stats or not video_id:
            logger.info(f'No content from item:\n{json_item}')
            return None
        self.total.append(f'{author_id}@{video_id}')
        if f"{author_id}@{video_id}" in self.uniq_ids:
            logger.info(f'Duplicated item: {author_id}@{video_id}')
            return None
        self.uniq_ids.add(f"{author_id}@{video_id}")
        return {
            'link': f"https://www.tiktok.com/@{author_id}/video/{video_id}",
            'upload': self._format_timestamp(json_item.get('createTime', '-')),
            'duration': json_item.get('video', {}).get('duration', '-'),
            'views': stats.get('playCount', '-'),
            'likes': stats.get('diggCount', '-'),
            'comments': stats.get('commentCount', '-'),
            'resend': stats.get('shareCount', '-'),
            'saves': stats.get('collectCount', '-'),
            "description": json_item.get('desc'),
        }

    @staticmethod
    def _save_to_csv(collected: list[CollectedItem], filename: str = 'report.csv'):
        file_path = Path(__file__).resolve().parent / filename
        fieldnames = ['link', 'upload', 'duration', 'views', 'likes', 'comments', 'resend', 'saves', 'description']
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(collected)

    @staticmethod
    def get_string_io(collected: list[CollectedItem]) -> io:
        fieldnames = ['link', 'upload', 'description', 'duration', 'views', 'likes', 'comments', 'resend', 'saves']
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(collected)
        output.seek(0)
        return output

    @staticmethod
    def _format_timestamp(timestamp):
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return '-'


if __name__ == '__main__':
    scrapper = TikTokScrapper()
    # asyncio.run(scrapper.run('https://www.tiktok.com/@phonkmusicxxl'))
    # asyncio.run(scrapper.run_by_user_uuid(
    #     sec_uid='MS4wLjABAAAAK2RRK-FRSh8Jj_0SW4Cbq3vXPkEArO9wiVIv2Gn9CpVdSJct_qzmrvvxqGRsY0K6')
    # )
    # asyncio.run(scrapper.run('https://www.tiktok.com/music/Scary-Garry-6914598970259490818'))

    """
    https://www.tiktok.com/@rxzxlx._.nation_
    MS4wLjABAAAAK2RRK-FRSh8Jj_0SW4Cbq3vXPkEArO9wiVIv2Gn9CpVdSJct_qzmrvvxqGRsY0K6
    
    https://www.tiktok.com/@djdannys_ 
    MS4wLjABAAAA9MGBOywKrH9Qd5YU2dx4gRweR19YdFGMjj4dluqFId5ebCKp5rdaWebIZr7JPDLF
    
    
    https://www.tiktok.com/@phonkmusicxxl 
    MS4wLjABAAAAz2_EHaznmB9JKgkaBgpoBPqKUh73k-eL7eH2netlM4esmWYbcTzIRzsBQMDCxVSo
    """