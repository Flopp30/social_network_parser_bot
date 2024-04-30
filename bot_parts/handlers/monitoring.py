import io
from typing import Any

import pandas as pd
from django.db.models import QuerySet
from telegram import Update
from telegram.ext import ContextTypes

from bot_parts.handlers.start import welcome_handler, start_handler
from bot_parts.helpers import WelcomeRedirectType
from bot_parts.messages import MESSAGE_MAP
from common.validators import LinkValidator


async def _get_monitoring_csv() -> io.StringIO:
    """Возвращает список ссылок в мониторинге в виде стрима csv"""
    # TODO нужен нормальный список после добавления мониторинга
    #  кажется, что это можно сделать как-то поаккуратнее, но я сходу не придумал.
    #  в целом, можно через async_to_sync, но мне этот декоратор нравится ещё меньше :(
    # links = [{'id': link.id, 'url': link.url} async for link in MonitoringLink.objects.filter(is_active=True)]
    links: list[dict] = [
        {"id": 2, "url": "https://www.youtube.com/watch?v=9bZkp7q19f0"},
        {"id": 3, "url": "https://www.youtube.com/watch?v=dass"},
    ]
    csv_output = io.StringIO()
    collection = pd.DataFrame(links)
    collection.to_string(csv_output, index=False)
    csv_output.seek(0)
    return csv_output


async def _get_monitoring_link_stat() -> tuple[int, int]:
    """Возвращает цифры статы по мониторингу"""
    # TODO нужны реальные цифры после мониторинга после добавления мониторинга
    #  подумать над полее сложной статой какой-нибудь, можно позже
    # is_active = await MonitoringLink.objects.filter(is_active=True).count()
    # total = await MonitoringLink.objects.count()
    is_active = 10
    total = 10
    return is_active, total


async def monitoring_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит callback с MONITORING_BOARD"""
    default_state: str = 'AWAIT_MONITORING_CHOICE'

    if not update.callback_query or update.callback_query.data not in ['add_link', 'remove_link', 'get_list', 'to_start']:
        return default_state

    if update.callback_query.data == 'to_start':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    if update.callback_query.data == 'get_list':
        # получение списка ссылок в мониторинге
        file: io.StringIO = await _get_monitoring_csv()
        is_active, total = await _get_monitoring_link_stat()
        caption = MESSAGE_MAP.get('monitoring_link_list_caption')

        if caption:
            caption = caption.format(is_active=is_active, total=total)

        await context.bot.send_document(
            update.effective_chat.id,
            document=file,
            caption=caption,
            filename='links.csv',
        )
        return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)

    state: str
    message_key: str
    if update.callback_query.data == 'add_link':
        # добавление ссылки в мониторинг
        message_key = 'monitoring_wait_link'
        state = 'MONITORING_AWAIT_LINK_FOR_ADDING'

    else:
        # удаление ссылки из мониторинга
        message_key = 'monitoring_wait_id_for_delete'
        state = 'MONITORING_AWAIT_ID_FOR_DELETING'

    message: str = MESSAGE_MAP.get(message_key)
    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )

    return state


async def ensure_monitoring_link(link: str) -> tuple[Any, bool]:
    """Обеспечивает ссылку в мониторинге (активирует/создает или просто возвращает, если уже есть)"""
    # TODO поправить тип возвращаемого значения после добавления мониторинга
    # link, create_flag = await MonitoringLink.objects.aget_or_create(link=link, defaults={"is_active": True})
    # if not create_flag and not link.is_active:
    #     link.is_active = True
    #     link.save(update_fields=["is_active"])
    # return link, create_flag
    return 'https://google.com', True


async def add_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет ссылки в мониторинг"""

    message_key: str
    dirty_link: str = update.message.text
    if decoded_link := LinkValidator.validate(dirty_link):
        link, created_flag = await ensure_monitoring_link(decoded_link)
        if created_flag:
            # TODO вот тут в двух format должно быть link.url, по идее
            #  Поправить после добавления мониторинга
            message_key = 'monitoring_link_added'
        else:
            message_key = 'monitoring_link_activated'

        message = MESSAGE_MAP.get(message_key)

        if message:
            message = message.format(link=link)
    else:
        message = MESSAGE_MAP.get('link_validation_error')

    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)


async def remove_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет ссылку из мониторинга"""
    # TODO после добавления мониторинга поправить удаление ссылки
    # link_params: dict[str: str | int] | None = None

    # message_key: str = 'monitoring_link_not_found'
    # try:
    #     # обрабатываем кейс по id
    #     link_params = {'id': int(update.message.text)}
    # except ValueError:
    #     # если не id - пытаемся по url
    #     if cleaned_link := LinkValidator.validate(update.message.text):
    #         link_params = {'url': cleaned_link}
    #     else:
    #         message_key = 'link_validation_error'
    #
    # if link_params:
    #     link_qs: QuerySet[MonitoringLink] = await MonitoringLink.objects.filter(**link_params)
    #     if (await link_qs.acount() != 1):
    #         message_key = 'monitoring_link_not_found'
    #     else:
    #         await link_qs.aupdate(is_active=False)
    #         message_key = 'monitoring_link_removed'

    # message = MESSAGE_MAP.get(message_key)
    message = MESSAGE_MAP.get('monitoring_link_removed')
    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)
