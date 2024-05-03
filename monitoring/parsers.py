import abc
import asyncio
import json
import logging
import re

import httpx

logger = logging.getLogger(__name__)


class VideoCountParser:
    """Базовый класс для парсеров количества видео со страницы"""
    YT_SCALE_MAP: dict = {
        'тыс.': 1_000,
        'млн.': 1_000_000,  # TODO потестить, не нашел сходу аккаунтов с таким количеством видео
    }
    TT_SCALE_MAP: dict = {
        'K': 1_000,
        'M': 1_000_000,
    }

    @abc.abstractmethod
    async def get_video_count(self, html_content: str) -> int | None:
        ...

    def _clean_yt_video_count(self, dirty_video_count: str) -> int | None:
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
                video_count = int(float(count.replace(',', '.')) * self.YT_SCALE_MAP.get(unit, 1))
                break

        return video_count


class YtMusicVideoCountParser(VideoCountParser):
    """Получает количество опубликованных видео со страницы звука"""

    async def get_video_count(self, html_content: str) -> int | None:
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
        return self._clean_yt_video_count(match_res)

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


class YtUserVideoCountParser(VideoCountParser):
    """Получает количество опубликованных видео со страницы пользователя (пока что всего, не только шортсов)"""

    async def get_video_count(self, html_content: str) -> int | None:
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
        return self._clean_yt_video_count(match_res)


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
    video_count: int | None = await parser.get_video_count(html_content)
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

    video_count: int | None = await parser.get_video_count(html_content)

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