import abc
import asyncio
import io
import json
import logging
import re
import time
from typing import Any

import httpx
import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)


def timer(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f'Время выполнения функции {func.__name__}: {execution_time} сек')
        return result

    return wrapper


class Finder:
    """Ищет значение по ключу в словарях и списках словарей"""

    def __init__(self):
        self.results: list = list()
        self.search_key = None

    def find(self, data: list | dict, search_key: str) -> list:
        self.results.clear()
        self.search_key = search_key

        if isinstance(data, list):
            self._find_in_list(data)
        elif isinstance(data, dict):
            self._find_in_dict(data)

        return self.results

    def _find_in_list(self, data: list):
        for item in data:
            if isinstance(item, list):
                self._find_in_list(item)
            if isinstance(item, dict):
                self._find_in_dict(item)

    def _find_in_dict(self, data: dict):
        for key, value in data.items():
            if key == self.search_key:
                self.results.append(value)
                continue
            if isinstance(value, dict):
                self._find_in_dict(value)
            if isinstance(value, list):
                self._find_in_list(value)

    def find_by_key_path(self, data: dict, key_path: list[str]) -> Any:
        """Ищет значение по ключам"""
        # TODO кажется, работает не очень корректно, т.к. в случае, если не находит - возвращается какое-то значение, а хотелось бы получать None
        #  подумать над более корректным вариантом
        while key_path:
            key = key_path.pop(0)
            if key in data:
                data = data.get(key)
            if isinstance(data, dict):
                continue
            if isinstance(data, list):
                data = self._find_by_key_path_list(data, key_path)
        return data

    def _find_by_key_path_list(self, data: list, key_path: list[str]) -> Any:
        for d in data:
            if isinstance(d, dict):
                data = self.find_by_key_path(d, key_path)
            if isinstance(d, list):
                self._find_by_key_path_list(d, key_path)
        return data


class HttpTelegramMessageSender:
    doc_url = settings.TELEGRAM_DOC_URL
    send_message_url = settings.TELEGRAM_MESSAGE_URL

    # doc_url = f"https://api.telegram.org/bot6288404871:AAHS6C29JiFkcrMspNkLxWB72_PLNO3K0V4/sendDocument"
    # send_message_url = f'https://api.telegram.org/bot6288404871:AAHS6C29JiFkcrMspNkLxWB72_PLNO3K0V4/sendMessage'

    @classmethod
    async def send_csv_doc(cls, chat_id: int, collection: dict | list | pd.DataFrame, caption: str, file_name: str = 'report.csv') -> str:
        """Отправляет отчет в tg"""
        if not isinstance(collection, pd.DataFrame):
            collection = pd.DataFrame(collection)

        string_io = io.StringIO()
        collection.to_csv(string_io, index=False)
        csv_data = string_io.getvalue().encode('utf-8')
        files = {
            "document": (file_name, csv_data, 'text/csv'),
        }
        params = {
            "chat_id": chat_id,
            "caption": caption,
        }
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(cls.doc_url, params=params, files=files)
                response.raise_for_status()
                logger.info(f"Report send with status {response.status_code}")
        except Exception as e:
            if response:
                logger.error(response.__dict__)
            logger.error(e)
            return 'With an error'

        return 'Ok'

    @classmethod
    async def send_text_message(cls, chat_id: int, text: str) -> str:
        """Отправляет текстовое сообщение в tg"""
        params = {
            "chat_id": chat_id,
            "text": text
        }
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(cls.send_message_url, json=params)
                response.raise_for_status()
                logger.info(f"Report send with status {response.status_code}")
        except Exception as e:
            if response:
                logger.error(response.__dict__)
            logger.error(e)
            return 'With an error'

        return 'Ok'


class YtVideoCountParser:
    SCALE_MAP = {
        'тыс.': 1_000,
        'млн.': 1_000_000,  # TODO потестить, не нашел сходу аккаунтов с таким количеством видео
    }

    @abc.abstractmethod
    def get_video_count(self, html_content: str) -> int | None:
        ...

    def _clean_video_count(self, dirty_video_count: str) -> int | None:
        """Возвращает количество видео из совпадения по регулярному выражению"""
        video_count: int | None = None
        # пробуем в инт сразу (если нет разделителей, то ок)
        try:
            return int(dirty_video_count)
        except ValueError:
            pass

        # разные разделите приходят
        for separator in ('\xa0', ' ', ' '):
            if separator in dirty_video_count:
                count, unit = dirty_video_count.split(separator)
                video_count = int(float(count.replace(',', '.')) * self.SCALE_MAP.get(unit, 1))
                break

        return video_count


class YtMusicVideoCountParser(YtVideoCountParser):
    """Получает количество опубликованных видео со страницы звука"""

    def get_video_count(self, html_content: str) -> int | None:
        """Возвращает количество видео по html коду страницы"""
        try:
            if video_count := self._parse_video_count_by_metadata(html_content):
                return video_count

            return self._parse_video_count_by_script(html_content)
        except Exception as e:
            logger.error(e)
            return None

    def _parse_video_count_by_metadata(self, html_content: str) -> int | None:
        """Получает количество видео из метадаты (кейсы, где есть указание количества видео под названием канала)"""
        match: re.Match[str] | None = re.search(r'\{"metadataParts":\[\{"text":\{"content":"(.*?)коротких видео', html_content)
        if not match:
            return None
        match_res: str = match.group(1).strip()
        return self._clean_video_count(match_res)

    def _parse_video_count_by_script(self, html_content: str) -> int | None:
        """Получает количество видео из скрипта"""
        # NOTE в кейсах, где видео мало, сверху заголовка нет :(
        # поэтому вытаскиваем из contents (js код, где инициализация объектов происходит для отрисовки)
        yt_data: re.Match[str]
        if not (yt_data := re.search(r'var ytInitialData = (.*?);</script>', html_content, re.DOTALL)):
            return None
        json_data: dict = json.loads(yt_data.group(1))

        # tabs - разделенные по группам видео на странице
        tabs: list = json_data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
        for tab in tabs:
            # contents - это список видео для отрисовки
            contents: list[dict | None] = tab.get('tabRenderer', {}).get('content', {}).get('richGridRenderer', {}).get('contents', [])
            for content in contents:
                # accessibility_text - текст для незрячих. Наличие там ключевого слова 'short' или 'короткое' указывает на то, что в этой вкладке лежат шортсы
                accessibility_text: str = content.get('richItemRenderer', {}).get('content', {}).get('shortsLockupViewModel', {}).get('accessibilityText')
                if 'короткое' in accessibility_text.lower() or 'short' in accessibility_text.lower():
                    return len(contents) + 1  # FIXME вот это чушь вообще, но по какой-то причине он ВСЕГДА возвращает (количество видео - 1)
        return None


class YtUserVideoCountParser(YtVideoCountParser):
    """Получает количество опубликованных видео со страницы пользователя (пока что всего, не только шортсов)"""

    def get_video_count(self, html_content: str) -> int | None:
        """Для безопасного извлечения - try except, но вероятно, тут надо ошибки половить в целом"""
        try:
            return self._parse_video_count_by_metadata(html_content)
        except Exception as e:
            logger.error(e)
            return None

    def _parse_video_count_by_metadata(self, html_content: str) -> int | None:
        match: re.Match[str] | None = re.search(r',"videosCountText":\{"runs":\[{"text":"(.*?)"},\{"text"', html_content)
        if not match:
            return None
        match_res: str = match.group(1).strip()
        return self._clean_video_count(match_res)


async def get_yt_music_video_count(url: str, client: httpx.AsyncClient, parser: YtMusicVideoCountParser) -> int | None:
    """Возвращает суммарное количество коротких видео для одного ютуб звука"""
    # TODO это пример использования, по аналогии нужно в MonitoringProcess.run() if MonitoringLink.source = youtube and 'source' in MonitoringLink.url
    try:
        resp: httpx.Response = await client.get(url)
        resp.raise_for_status()
    except Exception as e:
        logger.error(e)
        return None
    html_content: str = resp.text
    video_count: int | None = parser.get_video_count(html_content)
    return video_count


async def get_yt_user_video_count(url: str, client: httpx.AsyncClient, parser: YtUserVideoCountParser) -> int | None:
    """Возвращает количество суммарное количество видео для одного ютуб профиля"""
    # TODO это пример использования, по аналогии нужно в MonitoringProcess.run() if MonitoringLink.source = youtube and not 'source' in MonitoringLink.url
    try:
        resp: httpx.Response = await client.get(url)
        resp.raise_for_status()
    except Exception as e:
        logger.error(e)
        return None
    html_content: str = resp.text
    video_count: int | None = parser.get_video_count(html_content)
    return video_count


if __name__ == '__main__':
    async def yt_process():
        music_parser: YtMusicVideoCountParser = YtMusicVideoCountParser()
        profile_parser: YtUserVideoCountParser = YtUserVideoCountParser()
        async with httpx.AsyncClient() as client:
            link = 'https://www.youtube.com/source/d-XUjln47rg/shorts'
            video_count = await get_yt_music_video_count(link, client, music_parser)
            print(video_count)  # 65_000
            link = 'https://www.youtube.com/source/ZmKk4krdy84/shorts?bp=8gUeChwSGgoLWm1LazRrcmR5ODQSC1ptS2s0a3JkeTg0'
            video_count = await get_yt_music_video_count(link, client, music_parser)
            print(video_count)  # 4
            link = 'https://www.youtube.com/source/wFUKTERWOGM/shorts?bp=8gUeChwSGgoLd0ZVS1RFUldPR00SC3dGVUtURVJXT0dN'
            video_count = await get_yt_music_video_count(link, client, music_parser)
            print(video_count)  # 11_000

            # между запросами лучше слип по секунде хотя бы и несколько попыток на каждый запрос (для юзера)
            link = 'https://www.youtube.com/@officialphonkmusic'
            video_count = await get_yt_user_video_count(link, client, profile_parser)
            print(video_count)  # 183

            link = 'https://www.youtube.com/@varlamov'
            video_count = await get_yt_user_video_count(link, client, profile_parser)
            print(video_count)  # 1800


    # videosCountText
    asyncio.run(yt_process())
