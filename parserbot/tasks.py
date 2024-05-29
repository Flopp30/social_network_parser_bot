import asyncio
import logging

from celery import shared_task

from scrappers.tiktok.scrapper import TikTokScrapper
from scrappers.youtube.scrapper import YoutubeScrapper

logger = logging.getLogger('scrappers')


@shared_task(name='parse_tiktok_task')
def parse_tiktok(decoded_link, chat_id):
    scrapper = TikTokScrapper()
    try:
        res = asyncio.run(scrapper.run(decoded_link, chat_id=chat_id))
    except Exception as e:
        logger.error(e)
        res = f'{type(e).__name__}: {e}'
    return res


@shared_task(name='parse_tiktok_by_sec_uid')
def parse_tiktok_by_sec_uid(sec_uid, chat_id):
    scrapper = TikTokScrapper()
    try:
        res = asyncio.run(scrapper.run_by_user_uuid(sec_uid=sec_uid, chat_id=chat_id))
    except Exception as e:
        logger.error(e)
        res = f'{type(e).__name__}: {e}'
    return res


@shared_task(name='parse_yt_music_link')
def parse_yt_music_link(link, chat_id):
    scrapper = YoutubeScrapper()
    try:
        res = asyncio.run(scrapper.run(link, chat_id=chat_id))
    except Exception as e:
        logger.error(e)
        res = f'{type(e).__name__}: {e}'
    return res


@shared_task(name='parse_tt_one_video')
def parse_tt_one_video(link, chat_id):
    scrapper = TikTokScrapper()
    try:
        res = asyncio.run(scrapper.get_one_video_stat(chat_id=chat_id, url=link))
    except Exception as e:
        logger.error(e)
        res = f'{type(e).__name__}: {e}'
    return res
