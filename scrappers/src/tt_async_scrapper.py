import csv
import itertools
import logging
from datetime import datetime

import aiohttp
import asyncio
from parserbot.settings_requests import TikTokMusicScrapperConfig

logger = logging.getLogger('tiktok_scrapper')


class TikTokMusicScrapper:
    music_api_url = "https://www.tiktok.com/api/music/item_list/"

    def __init__(self):
        self.uniq_ids = set()
        self.start_cursors = [i for i in range(0, 10001, 500)]

    async def run(self, url):
        music_id = url.split('-')[-1].replace('/', '')
        start_time = datetime.now()
        tasks = []
        for start_cursor, cursor_breakpoint in zip(self.start_cursors[:-1], self.start_cursors[1:]):
            tasks.append(asyncio.create_task(self.request_process(start_cursor, cursor_breakpoint, music_id)))
        results = await asyncio.gather(*tasks)
        res = list(
            itertools.chain.from_iterable(results)
        )

        # async with asyncio.TaskGroup() as tg:
        #     tasks = {
        #         start_cursor: tg.create_task(self.request_process(start_cursor, cursor_breakpoint, music_id))
        #         for start_cursor, cursor_breakpoint in zip(self.start_cursors[:-1], self.start_cursors[1:])
        #     }
        # normalized_data = list(
        #     itertools.chain.from_iterable(
        #         (value.result() for key, value in tasks.items() if value.done()))
        # )
        finish_time = (datetime.now() - start_time).seconds
        print(f'Собрано {len(self.uniq_ids)} уникальных видео за {finish_time} сек')
        self._save_to_csv(collected=res)

    async def request_process(self, start_cursor, cursor_breakpoint, music_id):
        collected_items = []
        cursor = start_cursor
        while cursor < cursor_breakpoint:
            print(f'Запрос отправлен: {cursor} {cursor_breakpoint}')
            params = TikTokMusicScrapperConfig.params | {"musicID": music_id, "cursor": cursor}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        self.music_api_url,
                        headers=TikTokMusicScrapperConfig.headers,
                        cookies=TikTokMusicScrapperConfig.cookies,
                        params=params,
                ) as response:
                    if response.status != 200:
                        logger.error(f"[ {response.status} ] ERR {cursor}")
                        response.raise_for_status()
                    if not (serialized_data := await response.json()):
                        print('No content')
                        break
                    item_list = serialized_data.get('itemList', [])
                    for item in item_list:
                        if collected := self._parse_collected_from_json(item):
                            collected_items.append(collected)

            cursor = int(serialized_data.get('cursor'))
        return collected_items

    def _parse_collected_from_json(self, json_item: dict) -> dict | None:
        author_id = json_item.get('author', {}).get('uniqueId')
        video_id = json_item.get('id')
        stats = json_item.get('stats')
        if not author_id or not stats or not video_id or video_id in self.uniq_ids:
            return None
        self.uniq_ids.add(video_id)
        return {
            'link': f"https://www.tiktok.com/@{author_id}/video/{video_id}",
            'upload': json_item.get('createTime', '-'),
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


scrapper = TikTokMusicScrapper()
asyncio.run(scrapper.run('https://www.tiktok.com/music/Scary-Garry-6914598970259490818'))
