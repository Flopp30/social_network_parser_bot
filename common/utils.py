import asyncio
import io
import logging
import time
from functools import wraps
from typing import Any

import httpx
import pandas as pd
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def timer(print_logger: bool = False):
    def decorator(func):
        # Проверяем, является ли функция асинхронной
        if asyncio.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                result = await func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                if print_logger:
                    print(f'Время выполнения функции {func.__name__}: {execution_time:.4f} сек')
                else:
                    logger.info(f'Время выполнения функции {func.__name__}: {execution_time:.4f} сек')
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                if print_logger:
                    print(f'Время выполнения функции {func.__name__}: {execution_time:.4f} сек')
                else:
                    logger.info(f'Время выполнения функции {func.__name__}: {execution_time:.4f} сек')
                return result

            return sync_wrapper

    return decorator


def adaptive_threshold(current_count):
    if current_count < 500:
        return 0.50  # 50% рост
    elif current_count < 5000:
        return 0.25  # 25% рост
    else:
        return 0.10  # 10% рост


def analyze_growth(video_history: list[int]) -> float | None:
    if len(video_history) < 3:
        logger.error('Недостаточно данных для анализа.')
        return None

    weighted_growth_rate: float | None = compute_weighted_change(video_history)

    return weighted_growth_rate


def compute_weighted_change(history: list[int]) -> float | None:
    if len(history) < 3:
        logger.error('Недостаточно данных для анализа')
        return None
    try:
        changes: list[float] = [(history[i + 1] - history[i]) / history[i] for i in range(len(history) - 1)]
    except ZeroDivisionError:
        logger.error('compute_weighted_change: Деление на ноль')
        return None
    weights: list[int] = [i + 1 for i in range(len(changes))]
    weighted_change: float = sum(w * c for w, c in zip(weights, changes)) / sum(weights)
    return weighted_change


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

    def find_by_key_path(self, data: dict | list, key_path: list[str]) -> Any:
        """Ищет значение по ключам"""
        # TODO кажется, работает не очень корректно, т.к. в случае, если не находит - возвращается какое-то значение, а хотелось бы получать None
        #  подумать над более корректным вариантом
        while key_path:
            if isinstance(data, list):
                data = self._find_by_key_path_list(data, key_path)
            key = key_path.pop(0)
            if key in data:
                data = data.get(key)  # type: ignore
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
    # doc_url = 'https://api.telegram.org/bot6288404871:AAHS6C29JiFkcrMspNkLxWB72_PLNO3K0V4/sendDocument'
    # send_message_url = 'https://api.telegram.org/bot6288404871:AAHS6C29JiFkcrMspNkLxWB72_PLNO3K0V4/sendMessage'

    @classmethod
    async def send_csv_doc(cls, chat_id: int, collection: dict | list | pd.DataFrame, caption: str, file_name: str = 'report.csv') -> str:
        """Отправляет отчет в tg"""
        if not isinstance(collection, pd.DataFrame):
            collection = pd.DataFrame(collection)

        string_io = io.StringIO()
        collection.to_csv(string_io, index=False)
        csv_data = string_io.getvalue().encode('utf-8')
        files = {
            'document': (file_name, csv_data, 'text/csv'),
        }
        params = {
            'chat_id': chat_id,
            'caption': caption,
        }
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(cls.doc_url, params=params, files=files)
                response.raise_for_status()
                logger.info(f'Report send with status {response.status_code}')
        except Exception as e:
            error_msg = f'{type(e).__name__}: {e}'
            if response:
                logger.error(response.__dict__)
            logger.error(error_msg)
            return error_msg

        return 'Ok'

    @classmethod
    async def send_text_message(cls, chat_id: int, text: str) -> str:
        """Отправляет текстовое сообщение в tg"""
        params = {
            'chat_id': chat_id,
            'text': text,
        }
        response = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(cls.send_message_url, json=params)
                response.raise_for_status()
                logger.info(f'Report send with status {response.status_code}')
        except Exception as e:
            error_msg = f'{type(e).__name__}: {e}'
            if response:
                logger.error(response.__dict__)
            logger.error(error_msg)
            return error_msg

        return 'Ok'

    @classmethod
    def sync_send_text_message(cls, chat_id: int, text: str) -> str:
        """Синхронно отправляет текстовое сообщение в tg"""
        params = {
            'chat_id': chat_id,
            'text': text,
        }
        response = None
        try:
            response = requests.post(cls.send_message_url, json=params)
            response.raise_for_status()
            logger.info(f'Report send with status {response.status_code}')
        except Exception as e:
            error_msg = f'{type(e).__name__}: {e}'
            if response:
                logger.error(response.json())
            logger.error(error_msg)
            return error_msg

        return 'Ok'
