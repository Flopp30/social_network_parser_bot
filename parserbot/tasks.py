import asyncio

from celery import shared_task

from scrappers.tiktok.tt_async_scrapper import TikTokScrapper


@shared_task
def parse_tiktok(decoded_link, chat_id):
    scrapper = TikTokScrapper()
    asyncio.run(scrapper.run(decoded_link, tg_chat_id=chat_id))
