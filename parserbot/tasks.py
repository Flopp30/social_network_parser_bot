import asyncio
import logging

from celery import shared_task

from scrappers.tiktok.tt_async_scrapper import TikTokScrapper


logger = logging.getLogger('tiktok_scrapper')


@shared_task
def parse_tiktok(decoded_link, chat_id):
    scrapper = TikTokScrapper()
    try:
        res = asyncio.run(scrapper.run(decoded_link, tg_chat_id=chat_id))
    except Exception as e:
        logger.error(e)
        res = "with error"
    return res


@shared_task
def parse_tiktok_by_sec_uid(sec_uid, chat_id):
    scrapper = TikTokScrapper()
    try:
        res = asyncio.run(scrapper.run_by_user_uuid(sec_uid=sec_uid, tg_chat_id=chat_id))
    except Exception as e:
        logger.error(e)
        res = "with error"
    return res
