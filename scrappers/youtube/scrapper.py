import asyncio
import itertools
import json
import logging
import random
import re
from typing import TypedDict

import httpx
from setuptools._vendor.more_itertools.more import chunked

from common.utils import Finder, HttpTelegramMessageSender, timer
from common.validators import LinkValidator
from scrappers.youtube.request_params.params import get_yt_post_params

logger = logging.getLogger('youtube_scrapper')


class HtmlParseResult(TypedDict):
    json_data: dict
    query_params: str
    continuation_token: str
    visitor_id: str
    video_ids: list[str]


class CollectedItem(TypedDict):
    link: str
    views: int
    likes: int
    comments: int
    favourites: int
    id: str


class YoutubeScrapper:
    video_info_url: str = 'https://yt.lemnoslife.com/noKey/videos?part=id,statistics,snippet,contentDetails&id='
    info_api_chunk_size: int = 100
    info_api_timeout: int = 2

    yt_video_base_link = 'https://www.youtube.com/watch?v='
    yt_pagination_url = 'https://www.youtube.com/youtubei/v1/browse'

    # пути по ключам до нужной инфы для пагинации по видео (visitor_id, query параметры)
    VISITOR_DATA_PATH = ['responseContext', 'webResponseContextExtensionData', 'ytConfigData', 'visitorData']
    QUERY_PARAM_PATH = ['browseEndpoint', 'params']

    # диапазон слипа в пагинации
    PAGINATION_SLEEP_RANGE: tuple[float, float] = (1.0, 3.0)

    @timer
    async def run(self, link: str, chat_id: int):
        """Запуск парсера"""
        # валидируем ссылку
        if not (validated_link := LinkValidator.validate(link)):
            return await HttpTelegramMessageSender.send_text_message(chat_id, 'Неверная ссылка: ' + link)

        # получаем id связанных видео
        video_ids: set[str] = set()
        async with httpx.AsyncClient() as client:
            video_ids.update(await self._get_linked_video_ids(validated_link, client))
            logger.info('Video ids found: ' + str(len(video_ids)))

        if not video_ids:
            return await HttpTelegramMessageSender.send_text_message(chat_id, 'Видео не найдены: ' + link)

        tasks = []
        # получаем информацию о связанных видео по их id
        async with httpx.AsyncClient() as client:
            # итерируемся чанками, чтобы не спамить запросами в бесплатное API
            for chunk in chunked(video_ids, self.info_api_chunk_size):
                for video_id in chunk:
                    tasks.append(
                        asyncio.create_task(self.ger_videos_statistic_by_id(video_id, client))
                    )

                collected_items = await asyncio.gather(*tasks)
                # сохраняем инфу по видео в нормализованном виде
                normalized_items = list(itertools.chain.from_iterable(collected_items))
                # спим заданное время
                await asyncio.sleep(self.info_api_timeout)

        # если есть тг id - отправляем отчет
        return await HttpTelegramMessageSender.send_csv_doc(
            chat_id=chat_id,
            collection=normalized_items,
            caption='Отчет YT по ссылке: ' + link,
            file_name='yt_report.csv'
        )

    async def _get_linked_video_ids(self, link: str, client: httpx.AsyncClient) -> set[str]:
        """Возвращает id связанных видео"""
        found_ids: set[str] = set()  # type: ignore
        finder: Finder = Finder()

        # отправляем обычный запрос, чтобы получить html страницы
        try:
            response: httpx.Response = await client.get(link)
            response.raise_for_status()
        except Exception as e:
            logger.error(e)
            return found_ids

        # убираем ?bp из ссылки, если он там был (аттрибут отвечающий за идентичность запроса, так же передается в заголовках дальше)
        base_url = link.split('?bp=')[0]

        # разбираем ответ
        parse_result: HtmlParseResult | None = self._parse_html(finder, response.text)
        if parse_result is None:
            return found_ids

        # обновляем id видео
        found_ids.update(parse_result['video_ids'])
        prev_parsed_count: int = len(found_ids)

        # пагинация
        continuation_token: str = parse_result['continuation_token']
        attempt_counter: int = 3

        while continuation_token is not None and attempt_counter > 0:
            # спим между запросами
            await asyncio.sleep(random.uniform(*self.PAGINATION_SLEEP_RANGE))

            json_data: dict | None = await self.pagination_post_request(
                base_url,
                parse_result['query_params'],
                parse_result['visitor_id'],
                continuation_token,
                client
            )
            if not json_data:
                logger.info('Empty response')
                attempt_counter -= 1
                continue

            # ищем новый токен пагинации
            new_token = finder.find(json_data, 'token')
            if new_token:
                continuation_token = new_token[0]

            # ищем все videoId в словаре
            found_ids.update(finder.find(json_data, 'videoId'))

            # чек на случай бесконечного цикла. По идее такой ситуации быть не должно
            if prev_parsed_count == len(found_ids):
                attempt_counter -= 1

            prev_parsed_count = len(found_ids)

        return found_ids

    def _parse_html(self, finder: Finder, html_content: str) -> HtmlParseResult | None:
        """Парсит информацию со страницы ютуба"""
        # ytInitialData (без неё не имеет смысла продолжать, т.к. именно отсюда получаем токен пагинации)
        yt_data: re.Match[str] = re.search(r'var ytInitialData = (.*?);</script>', html_content, re.DOTALL)
        if not yt_data:
            return None
        json_data: dict = json.loads(yt_data.group(1))

        # тут лежит идентификатор уникальности запроса
        yt_command: dict | list = json.loads(re.search(r'window\[\'ytCommand\'\] = ({.*?});', html_content).group(1))

        query_params = finder.find_by_key_path(yt_command, self.QUERY_PARAM_PATH)
        if not isinstance(query_params, str):
            query_params = finder.find(query_params, 'params')
            if query_params:
                query_params = query_params[0]
        assert query_params is not None and isinstance(query_params, str)

        # visitor_id
        visitor_id = finder.find_by_key_path(json_data, self.VISITOR_DATA_PATH)
        if not isinstance(visitor_id, str):
            visitor_id = finder.find(visitor_id, 'visitorData')
            if visitor_id:
                visitor_id = visitor_id[0]
        assert visitor_id is not None and isinstance(visitor_id, str)

        # token пагинации
        continuation_token: list[str] = finder.find(json_data, 'token')
        continuation_token: str = continuation_token[0] if continuation_token else None

        # ищем id видео
        video_ids: list[str] = finder.find(json_data, 'videoId')
        return HtmlParseResult(
            json_data=json_data,
            query_params=query_params,
            visitor_id=visitor_id,
            continuation_token=continuation_token,
            video_ids=video_ids
        )

    async def ger_videos_statistic_by_id(self, video_id: str, client: httpx.AsyncClient) -> list[CollectedItem]:
        """Получает статистику по одному видео по его id"""
        attempt_counter = 3
        response: httpx.Response | None = None

        while attempt_counter > 0 and not response:
            try:
                response = await client.get(self.video_info_url + video_id)
                response.raise_for_status()
            except Exception:
                attempt_counter -= 1

        if response and (json_data := response.json().get('items')):
            return [self._get_collected_item(item) for item in json_data]

        return []

    def _get_collected_item(self, item: dict) -> CollectedItem:
        statistic: dict = item.get('statistics', {})
        return CollectedItem(
            link=self.yt_video_base_link + item.get('id'),
            views=statistic.get('viewCount'),
            likes=statistic.get('likeCount'),
            comments=statistic.get('commentCount'),
            favourites=statistic.get('favoriteCount'),
            id=item.get('id'),
        )

    async def pagination_post_request(self, base_url: str, query_params: str, visitor_data: str, continuation: str, client: httpx.AsyncClient) -> dict | None:
        headers, cookie, params, post_data = get_yt_post_params(base_url, query_params, visitor_data, continuation)
        try:
            response: httpx.Response = await client.post(self.yt_pagination_url, headers=headers, cookies=cookie, params=params, json=post_data)
            response.raise_for_status()
        except Exception as e:
            logger.error(e)
            return None
        return response.json()


if __name__ == '__main__':
    asyncio.run(YoutubeScrapper().run('https://www.youtube.com/source/d-XUjln47rg/shorts', chat_id=434389137))
