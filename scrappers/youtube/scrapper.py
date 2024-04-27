import asyncio
import itertools
import json
import logging
import re
from typing import TypedDict

import httpx

from common.utils import Finder, HttpTelegramMessageSender
from common.validators import LinkValidator
from scrappers.youtube.request_params.params import get_yt_post_params

logger = logging.getLogger('youtube_scrapper')


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

    # пути по ключам до нужной инфы для пагинации по видео (continuation_token, visitor_id, query параметры)
    VISITOR_DATA_PATH = ['responseContext', 'webResponseContextExtensionData', 'ytConfigData', 'visitorData']
    QUERY_PARAM_PATH = ['browseEndpoint', 'params']

    # временное ограничение на тестирование
    MAX_ITEM_COLLECTED_COUNT: int = 4000

    # вроде не нужен, но пусть полежит сохраненный какое-то время.
    # CONTINUATION_TOKEN_PATH = ['contents', 'twoColumnBrowseResultsRenderer', 'tabs', 'tabRenderer', 'content', 'richGridRenderer', 'contents',
    #                            'continuationItemRenderer', 'continuationEndpoint', 'continuationCommand', 'token']

    async def run(self, link: str, chat_id: int | None = None):
        """Запуск парсера"""
        # валидируем ссылку
        if not (validated_link := LinkValidator.validate(link)):
            return await HttpTelegramMessageSender.send_text_message(chat_id, 'Неверная ссылка: ' + link)

        # получаем id связанных видео
        video_ids = await self._get_linked_video_ids(validated_link)
        if not video_ids:
            return await HttpTelegramMessageSender.send_text_message(chat_id, 'Видео не найдены: ' + link)

        video_ids = list(video_ids)  # нужно, чтобы дальше чанками пройтись
        tasks = []
        normalized_items = []
        # получаем информацию о связанных видео по их id
        async with httpx.AsyncClient() as client:
            # итерируемся чанками, чтобы не спамить запросами в бесплатное API
            while True:
                chunk = video_ids[:self.info_api_chunk_size]
                if not chunk:
                    break
                video_ids = video_ids[self.info_api_chunk_size:]
                for video_id in chunk:
                    tasks.append(
                        asyncio.create_task(self.ger_videos_statistic_by_id(video_id, client))
                    )

                collected_items = await asyncio.gather(*tasks)
                # сохраняем инфу по видео в нормализованном виде
                normalized_items += list(itertools.chain.from_iterable(collected_items))
                # спим заданное время
                await asyncio.sleep(self.info_api_timeout)

        # если есть тг id - отправляем отчет
        if chat_id:
            return await HttpTelegramMessageSender.send_csv_doc(chat_id, normalized_items, 'Отчет YT по ссылке: ' + link)

    async def _get_linked_video_ids(self, link: str) -> set[str]:
        """Возвращает id связанных видео"""
        found_ids: set[str] = set()  # type: ignore
        finder: Finder = Finder()
        async with httpx.AsyncClient() as client:
            # отправляем обычный запрос, чтобы получить html страницы
            response: httpx.Response = await client.get(link)
            response.raise_for_status()

            # убираем ?bp из ссылки, если он там был (аттрибут отвечающий за идентичность запроса, так же передается в заголовках дальше)
            base_url = link.split('?bp=')[0]
            # разбираем ответ
            html_data = response.text

            # ищем query параметры для пагинации
            yt_command = json.loads(re.search(r'window\[\'ytCommand\'\] = ({.*?});', html_data).group(1))
            query_params = finder.find_by_key_path(yt_command, self.QUERY_PARAM_PATH)

            # ищем yt initial data, чтобы оттуда получить id связанных видео и метаинфу для пагинации
            yt_data = re.search(r'var ytInitialData = (.*?);</script>', html_data, re.DOTALL)
            if not yt_data:
                return found_ids
            json_data: dict = json.loads(yt_data.group(1))
            # visitor_id
            visitor_data = finder.find_by_key_path(json_data, self.VISITOR_DATA_PATH)

            # токен пагинации (вроде в запросах только один токен возвращается). Но на всякий случай путь до него сохранил в параметре класса.
            continuation_token = finder.find(json_data, 'token')
            continuation_token = continuation_token[0] if continuation_token else None

            # ищем все videoId в словаре
            found_ids.update(finder.find(json_data, 'videoId'))

            # пагинация
            while continuation_token:
                json_data: dict = await self.pagination_post_request(base_url, query_params, visitor_data, continuation_token, client)
                # ищем новый токен пагинации
                continuation_token = finder.find(json_data, 'token')
                continuation_token = continuation_token[0] if continuation_token else None
                # ищем все videoId в словаре
                found_ids.update(finder.find(json_data, 'videoId'))
                logger.info(f'Найдено {len(found_ids)} видео')

                # TODO временный блок на время тестирования
                if len(found_ids) > self.MAX_ITEM_COLLECTED_COUNT:
                    break

        return found_ids

    async def ger_videos_statistic_by_id(self, video_id: str, client: httpx.AsyncClient) -> list[CollectedItem]:
        """Получает статистику по одному видео по его id"""
        response: httpx.Response = await client.get(self.video_info_url + video_id)
        response.raise_for_status()
        if not (json_data := response.json().get('items')):
            return []

        return [self._get_collected_item(item) for item in json_data]

    def _get_collected_item(self, item: dict) -> CollectedItem:
        return CollectedItem(
            link=self.yt_video_base_link + item['id'],
            views=item['statistics']['viewCount'],
            likes=item['statistics']['likeCount'],
            comments=item['statistics']['commentCount'],
            favourites=item['statistics']['favoriteCount'],
            id=item['id'],
        )

    async def pagination_post_request(self, base_url: str, query_params: str, visitor_data: str, continuation: str, client: httpx.AsyncClient) -> dict:
        headers, cookie, params, post_data = get_yt_post_params(base_url, query_params, visitor_data, continuation)
        response: httpx.Response = await client.post(self.yt_pagination_url, headers=headers, cookies=cookie, params=params, json=post_data)
        response.raise_for_status()
        return response.json()
