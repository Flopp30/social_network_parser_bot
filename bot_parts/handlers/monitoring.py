import io
from typing import TYPE_CHECKING

import pandas as pd
from telegram import Update
from telegram.ext import ContextTypes

from bot_parts.handlers.start import start_handler, welcome_handler
from bot_parts.helpers import WelcomeRedirectType
from bot_parts.messages import MessageContainer
from common.validators import LinkValidator, ValidationScopes
from monitoring.models import MonitoringLink
from monitoring.utils import ensure_monitoring_link

if TYPE_CHECKING:
    from django.db.models import QuerySet


async def _get_monitoring_csv() -> io.StringIO | None:
    """Возвращает список ссылок в мониторинге в виде стрима csv"""
    links = [{'id': link.id, 'url': link.url} async for link in MonitoringLink.objects.filter(is_active=True)]
    if not links:
        return None
    csv_output = io.StringIO()
    collection = pd.DataFrame(links)
    collection.to_string(csv_output, index=False)
    csv_output.seek(0)
    return csv_output


async def _get_monitoring_link_stat() -> tuple[int, int]:
    """Возвращает цифры статы по мониторингу"""
    # TODO подумать над более вразумительной статой
    is_active = await MonitoringLink.objects.filter(is_active=True).acount()
    total = await MonitoringLink.objects.acount()
    return is_active, total


async def monitoring_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловит callback с MONITORING_BOARD"""
    default_state: str = 'AWAIT_MONITORING_CHOICE'

    if not update.callback_query or update.callback_query.data not in ['add_link', 'remove_link', 'get_list', 'to_start_from_monitoring']:
        return default_state

    if update.callback_query.data == 'to_start_from_monitoring':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    if update.callback_query.data == 'get_list':
        # получение списка ссылок в мониторинге
        file: io.StringIO | None = await _get_monitoring_csv()

        if file is None:
            await context.bot.send_message(
                update.effective_chat.id,
                text=MessageContainer.monitoring_link_list_empty,
            )
            return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)

        is_active, total = await _get_monitoring_link_stat()
        caption = MessageContainer.monitoring_link_list_caption

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
    if update.callback_query.data == 'add_link':
        # добавление ссылки в мониторинг
        message = MessageContainer.monitoring_wait_link
        state = 'MONITORING_AWAIT_LINK_FOR_ADDING'

    else:
        # удаление ссылки из мониторинга
        message = MessageContainer.monitoring_wait_id_for_delete
        state = 'MONITORING_AWAIT_ID_FOR_DELETING'

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )

    return state


async def ensure_monitoring_links(urls: list[str]) -> str:
    """Обеспечивает ссылки в мониторинге (активирует/создает или просто возвращает, если уже есть)"""
    cleaned_urls = set(filter(lambda x: x is not None, [LinkValidator.validate(url, scopes=ValidationScopes.MONITORING) for url in urls]))
    # TODO отрефакторить.. Это чушь полная
    created_count = 0
    activated_count = 0

    for url in cleaned_urls:
        if url is None:
            continue

        _, created_flag = await ensure_monitoring_link(url)
        if created_flag:
            created_count += 1
        else:
            activated_count += 1

    if len(urls) == 1:
        if cleaned_urls:
            return MessageContainer.monitoring_add_link.format(link=cleaned_urls.pop())
        return MessageContainer.link_validation_error.format(link=urls[0])

    return MessageContainer.monitoring_add_multiple_links.format(
        success_count=len(cleaned_urls),
        created_count=created_count,
        activated_count=activated_count,
        invalid_count=len(urls) - len(cleaned_urls),
    )


async def add_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет ссылки в мониторинг"""
    dirty_urls: list[str]
    if '\n' in update.message.text:
        dirty_urls = update.message.text.split('\n')
    else:
        dirty_urls = update.message.text.split(' ')

    message: str = await ensure_monitoring_links(dirty_urls)

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)


async def remove_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет ссылку из мониторинга"""

    link_params: dict[str, str | int] | None = None
    message: str = MessageContainer.link_validation_error
    try:
        # обрабатываем кейс по id
        link_params = {'id': int(update.message.text)}
    except ValueError:
        # если не id - пытаемся по url
        if cleaned_url := LinkValidator.validate(update.message.text, scopes=ValidationScopes.MONITORING):
            link_params = {'url': cleaned_url}
        else:
            message = MessageContainer.link_validation_error.format(link=update.message.text)

    if link_params:
        link_qs: QuerySet[MonitoringLink] = MonitoringLink.objects.filter(**link_params)
        if await link_qs.acount() != 1:
            message = MessageContainer.monitoring_link_not_found
        else:
            await link_qs.aupdate(is_active=False)
            message = MessageContainer.monitoring_link_removed

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.MONITORING)
