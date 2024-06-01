"""
Подсмотреть, откуда берутся те или иначе значения можно в tiktok-signature/examples
"""

import abc
import logging
from copy import deepcopy
from json import JSONDecodeError
from urllib.parse import urlencode

import aiohttp
from django.conf import settings

logger = logging.getLogger(__name__)


class TiktokSignatureABC(abc.ABC):
    """Базовый класс для получения x-tt-params при запросах к апи пользователей."""

    # url локально развернутого сервиса сигнатуры
    local_signature_url: str = settings.TT_SIGNATURE_URL
    # tt api point
    api_url: str
    # query параметры
    params: dict
    # дефолтные headers для запроса уже после подписания (к ним добавляем x-tt-params)
    default_headers: dict

    @classmethod
    async def get_request_headers(cls, sec_uid: str, cursor: int) -> dict[str, str] | None:
        if not (x_tt_params := await cls.get_tt_params(sec_uid, cursor)):
            return None
        return cls.default_headers | {'x-tt-params': x_tt_params}

    @classmethod
    async def get_tt_params(cls, sec_uid: str, cursor: int) -> str | None:
        params: dict = deepcopy(cls.params) | {'cursor': cursor, 'secUid': sec_uid}
        fake_user_url: str = cls.api_url + urlencode(params)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.local_signature_url,
                headers={'Content-type': 'application/json'},
                data=fake_user_url,
            ) as response:
                try:
                    serialized_data: dict = await response.json()
                except JSONDecodeError:
                    logger.error('Error in the response from the internal service (signer)')
                    return None
            return serialized_data.get('data', {}).get('x-tt-params')


class UserVideoTiktokSignature(TiktokSignatureABC):
    """Получение x-tt-params по видео из аккаунта пользователя"""

    api_url: str = 'https://m.tiktok.com/api/post/item_list/?'
    params: dict = {
        'aid': '1988',
        'count': 30,
        'cookie_enabled': 'true',
        'screen_width': 0,
        'screen_height': 0,
        'browser_language': '',
        'browser_platform': '',
        'browser_name': '',
        'browser_version': '',
        'browser_online': '',
        'timezone_name': 'Europe/London',
    }
    default_headers = {
        'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.56'),
    }
