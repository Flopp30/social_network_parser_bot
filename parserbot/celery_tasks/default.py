# TODO пока пусть будет так, но вообще их надо будет по приложениям разнести, когда их станет побольше

import asyncio
import logging

from common.celery import default_celery_task, long_celery_task
from scrappers.tiktok.scrapper import TikTokScrapper
from scrappers.youtube.scrapper import YoutubeScrapper

logger = logging.getLogger('scrappers')


@default_celery_task(name='parse_tt')
def parse_tiktok(link, chat_id):
    scrapper = TikTokScrapper()
    return asyncio.run(scrapper.run(link, chat_id=chat_id))


@long_celery_task(name='parse_tt_with_geo')
def parse_tt_with_get(link, chat_id):
    scrapper = TikTokScrapper()
    return asyncio.run(scrapper.run(link, chat_id=chat_id, with_geo=True))


@default_celery_task(name='parse_tt_by_sec_uid')
def parse_tiktok_by_sec_uid(sec_uid, chat_id):
    scrapper = TikTokScrapper()
    return asyncio.run(scrapper.run_by_user_uuid(sec_uid=sec_uid, chat_id=chat_id))


@default_celery_task(name='parse_yt_music_link')
def parse_yt_music_link(link, chat_id):
    scrapper = YoutubeScrapper()
    return asyncio.run(scrapper.run(link, chat_id=chat_id))


@default_celery_task(name='parse_tt_one_video')
def parse_tt_one_video(link, chat_id):
    scrapper = TikTokScrapper()
    return asyncio.run(scrapper.get_one_video_stat(chat_id=chat_id, url=link))
