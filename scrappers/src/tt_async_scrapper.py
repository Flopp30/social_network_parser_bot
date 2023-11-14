import asyncio
import copy
import csv
import itertools
import logging
import random
import re
import time
from datetime import datetime
from json import JSONDecodeError
from urllib.parse import urlencode

import aiohttp
import httpx
import requests

from parserbot.settings_requests.models import SCRAPPER_SETTINGS
from parserbot.settings_requests.settings_instances import *

logger = logging.getLogger('tiktok_scrapper')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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

CONSTANT_MUSIC_API_URL = """
     https://m.tiktok.com/api/music/item_list/
     ?aid=1988&app_language=en
     &app_name=tiktok_web
     &battery_info=1
     &browser_language=en-US
     &browser_name=Mozilla
     &browser_online=true
     &browser_platform=Win32
     &browser_version=5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F101.0.4951.64%20Safari%2F537.36%20Edg%2F101.0.1210.53
     &channel=tiktok_web
     &cookie_enabled=true
     &device_id=7002566096994190854
     &device_platform=web_pc&focus_state=false
     &from_page=music&history_len=1
     &is_fullscreen=false&is_page_visible=true&os=windows
     &priority_region=RO&referer=&region=RO
     &screen_height=1080
     &screen_width=1920
     &tz_name=Europe%2FBucharest
     &verifyFp=verify_dca8729afe5c502257ed30b0b070dbdb
     &webcast_language=en
     &msToken=K8Xf-t_4RZ5n27zHsUPRyDIjpHQtfPeuHSvtbWzz0D0CQkX1UEyEdV0Xgx5BdbFPqKZ2McVCdlo1RM_u3o9FRglKoFa7TLZz2Yhd_fYRgWKhQDAq1TxQwLSTCz7Jp-EzVhopdNFO
     &X-Bogus=DFSzswVOLbUANCTQSwQvy2XyYJAm
     &_signature=_02B4Z6wo00001S9DBBwAAIDADOIqsG3-iK0vQwCAAClJd0
    """.replace("\n", "").replace(' ', '')  # DON'T TOUCH THIS VARIABLE

DEFAULT_PARAMS = {
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
}
NODE_URL = 'http://localhost/signature'


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
    user_api_url = "https://www.tiktok.com/api/post/item_list/"
    CONFIGS = SCRAPPER_SETTINGS.get('tiktok')

    def __init__(self):
        self.uniq_ids = set()
        self.total = list()
        self.request_counter = 0

    @timer
    async def run(self, url: str):
        if 'music' in url:
            music_id = int(url.split('-')[-1].replace('/', ''))
            cursors = [i for i in range(0, 5001, 500)]
            start_slicer = 0
            finish_slicer = len(cursors) // len(self.CONFIGS)
            async with asyncio.TaskGroup() as task_group:
                tasks = []
                for config in self.CONFIGS:
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
            # tasks = []
            # for start_cursor, cursor_breakpoint in zip(cursors[:-1], cursors[1:]):
            #     tasks.append(
            #         asyncio.create_task(
            #             self.new_request_music_process(music_id, start_cursor, cursor_breakpoint)
            #         )
            #     )
            # await asyncio.gather(*tasks)
            normalized_data = list(
                itertools.chain.from_iterable(
                    (task.result() for task in tasks if task.done()))
            )
            file_name = 'music_report.csv'
        else:
            sec_uid = await self._get_sec_uid_from_url(url)
            normalized_data = await self._request_user_process(sec_uid)
            file_name = 'user_report.csv'

        logger.info(f'Собрано {len(self.uniq_ids)} уникальных видео')
        logger.info(f'Всего собрано {len(self.total)} видео')
        self._save_to_csv(collected=normalized_data, filename=file_name)

    async def _request_user_process(self, sec_uid):
        collected_items = []
        cursor = 0
        while True:
            serialized_data = await self._scrape_user_page(sec_uid, cursor)
            for item in serialized_data.get('itemList', []):
                if collected := self._parse_collected_from_json(item):
                    collected_items.append(collected)

            cursor = serialized_data.get('cursor')
            if not serialized_data.get('hasMore'):
                logger.debug(f'Limit: {cursor}')
                break
        return collected_items

    @staticmethod
    async def _scrape_user_page(sec_uid: str, cursor: int):
        params = copy.deepcopy(DEFAULT_PARAMS) | {"secUid": sec_uid, "cursor": cursor}
        fake_user_url = f"https://m.tiktok.com/api/post/item_list/?" + urlencode(params)
        async with aiohttp.ClientSession() as session:
            async with session.post(NODE_URL, headers={'Content-type': 'application/json'}, data=fake_user_url) as response:
                try:
                    data = await response.json()
                except JSONDecodeError:
                    logger.error('Error in the response from the internal service (signer)')
                    return {}
                if not (tt_params := data.get('data', {}).get('x-tt-params')):
                    logger.error(f'tt_params not found in {data}')
                    return {}
        headers = {
            "x-tt-params": tt_params,
            'user-agent': (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56"
            ),
        }

        response = requests.get(CONSTANT_USER_API_URL, headers=headers)
        if response.status_code != 200:
            logger.error(f"[ {response.status_code} ] ERR {cursor} :\n{response.text}")
            return {}

        try:
            serialized_data = response.json()
        except JSONDecodeError:
            logger.debug(f'No content:\n{response.text}')
            return {}
        return serialized_data

    async def _request_music_process(
            self,
            headers: dict[str:str],
            cookies: dict[str:str],
            params: dict[str: str],
            start_cursor: int,
            cursor_breakpoint: int,
    ):
        collected_items = []
        cursor = start_cursor
        async with aiohttp.ClientSession() as session:
            while cursor < cursor_breakpoint:
                # await asyncio.sleep(random.randint(1, 10))
                logger.debug(f'Запрос отправлен: {cursor} : {cursor_breakpoint}')
                params |= {"cursor": cursor}
                async with session.get(
                        self.music_api_url,
                        headers=headers,
                        cookies=cookies,
                        params=params,
                ) as response:
                    if response.status != 200:
                        logger.error(f"[ {response.status} ] ERR {cursor} :\n{await response.text()}")
                        response.raise_for_status()

                    if not (serialized_data := await response.json()):
                        logger.debug(f'No content:\n{await response.text()}')
                        logger.debug(response)
                        break

                    if (new_ms_token := response.cookies.get('msToken')):
                        cookies |= {"msToken": new_ms_token.value}
                        params |= {"msToken": new_ms_token.value}

                    for item in serialized_data.get('itemList', []):
                        if collected := self._parse_collected_from_json(item):
                            collected_items.append(collected)

                if not serialized_data.get('hasMore'):
                    logger.debug(f'Limit: {cursor}')
                    break
                cursor = int(serialized_data.get('cursor'))
        return collected_items

    async def new_request_music_process(self, music_id, start_cursor, cursor_breakpoint):
        collected_items = []
        cursor = start_cursor
        while int(cursor) < cursor_breakpoint:
            serialized_data = await self.scrape_music_page(music_id, cursor)
            for item in serialized_data.get('itemList', []):
                if collected := self._parse_collected_from_json(item):
                    collected_items.append(collected)

            cursor = serialized_data.get('cursor')
            if not serialized_data.get('hasMore'):
                logger.debug(f'Limit: {cursor}')
                break
        return collected_items

    @staticmethod
    async def scrape_music_page(music_id, cursor):
        params = copy.deepcopy(DEFAULT_PARAMS) | {"musicID": music_id, "cursor": cursor}
        fake_music_url = f"https://m.tiktok.com/api/music/item_list/?" + urlencode(params)
        async with aiohttp.ClientSession() as session:
            async with session.post(NODE_URL, headers={'Content-type': 'application/json'}, data=fake_music_url) as response:
                try:
                    data = await response.json()
                except JSONDecodeError:
                    logger.error('Error in the response from the internal service (signer)')
                    return {}
                if not (tt_params := data.get('data', {}).get('x-tt-params')):
                    logger.error(f'tt_params not found in {data}')
                    return {}
        headers = {
            "x-tt-params": tt_params,
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56",
        }
        client = httpx.AsyncClient(timeout=10)
        response = await client.get(CONSTANT_MUSIC_API_URL, headers=headers)
        if response.status_code != 200:
            logger.error(f"[ {response.status_code} ] ERR {cursor} :\n{response.text}")
            return {}

        try:
            serialized_data = response.json()
        except JSONDecodeError:
            logger.debug(f'No content:\n{response.text}')
            return {}
        return serialized_data

    @staticmethod
    async def _get_sec_uid_from_url(url: str) -> str | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if not response.status == 200:
                    logger.error(f"Failed to get page content from {url}. Status code: {response.status}")
                    return None

                content = await response.text()
                pattern = r'"secUid":"(.*?)"'
                if (match := re.search(pattern, content)):
                    sec_uid = match.group(1)
                    return sec_uid
                else:
                    logger.error(f"Failed to find secUid on the page from url {url}.")
                    return None

    def _parse_collected_from_json(self, json_item: dict) -> dict | None:
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
            "description": json_item.get('desc'),
            'duration': json_item.get('video', {}).get('duration', '-'),
            'views': stats.get('playCount', '-'),
            'likes': stats.get('diggCount', '-'),
            'comments': stats.get('commentCount', '-'),
            'resend': stats.get('shareCount', '-'),
            'saves': stats.get('collectCount', '-'),
        }

    @staticmethod
    def _save_to_csv(collected: list[dict], file_path: str = '', filename: str = 'report.csv'):
        fieldnames = ['link', 'upload', 'description', 'duration', 'views', 'likes', 'comments', 'resend', 'saves']
        with open(f'{file_path}{filename}', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(collected)

    @staticmethod
    def _format_timestamp(timestamp):
        if timestamp == '-':
            return '-'
        else:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')


scrapper = TikTokScrapper()
asyncio.run(scrapper.run('https://www.tiktok.com/@domixx007'))
# asyncio.run(scrapper.run('https://www.tiktok.com/music/Scary-Garry-6914598970259490818'))
