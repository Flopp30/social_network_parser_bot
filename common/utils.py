import io
import logging
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
        # TODO кажется, работает не очень корректно, т.к. в случае, если она не находит - возвращается как-то значение, а хотелось бы получать None
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
                response = await client.post(settings.TELEGRAM_DOC_URL, params=params, files=files)
                response.raise_for_status()
                logger.info(f"Report send with status {response.status_code}")
        except Exception as e:
            logger.error(response.__dict__)
            logger.error(e)
            return 'With an error'

        return 'Ok'

    @classmethod
    async def send_text_message(cls, chat_id: int, text: str) -> str:
        """Отправляет тестовое сообщение в tg"""
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
            logger.error(response.__dict__)
            logger.error(e)
            return 'With an error'

        return 'Ok'
