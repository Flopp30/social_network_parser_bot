import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from bot_parts.handlers.start import start_handler, welcome_handler
from bot_parts.helpers import WelcomeRedirectType, check_bot_context
from bot_parts.messages import MessageContainer
from common.validators import LinkValidator, ValidationScopes
from parserbot.celery_tasks import parse_tiktok, parse_tiktok_by_sec_uid, parse_tt_one_video, parse_yt_music_link, parse_tt_with_get


async def add_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задачу на парсинг ссылки | id (для тиктока)"""
    await check_bot_context(update, context)

    # редирект назад
    if update.callback_query and update.callback_query.data == 'to_start_from_parsing':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    dirty_link: str = update.message.text
    if decoded_link := LinkValidator.validate(dirty_link):
        if 'tiktok' in decoded_link:
            parse_tiktok.apply_async(args=[decoded_link, update.effective_chat.id])
        elif 'youtube' in decoded_link:
            parse_yt_music_link.apply_async(args=[decoded_link, update.effective_chat.id])
        message = MessageContainer.parsing_success

    elif dirty_link.startswith('MS'):
        # парсинг по sec_uid (для тиктока)
        parse_tiktok_by_sec_uid.apply_async(args=[update.message.text.strip(), update.effective_chat.id])
        message = MessageContainer.parsing_by_sec_uid
    else:
        message = MessageContainer.link_validation_error.format(link=dirty_link)

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )
    await asyncio.sleep(1)
    # возвращает редирект на welcome_handler
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.PARSING)


async def parsing_with_geo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение статистики с гео. Доступен только для тиктока"""
    await check_bot_context(update, context)

    # редирект назад
    if update.callback_query and update.callback_query.data == 'to_start_from_geo_parsing':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    dirty_link: str = update.message.text
    if decoded_link := LinkValidator.validate(dirty_link, scopes=[ValidationScopes.TIKTOK_USER, ValidationScopes.TIKTOK_MUSIC]):
        parse_tt_with_get.apply_async(args=[decoded_link, update.effective_chat.id])
        message = MessageContainer.parsing_success
    else:
        message = MessageContainer.link_validation_error.format(link=dirty_link)

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )
    await asyncio.sleep(1)
    # возвращает редирект на welcome_handler
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.GEO_PARSING)


async def one_link_stat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение статистики для одного видео по ссылке"""
    await check_bot_context(update, context)

    # редирект назад
    if update.callback_query and update.callback_query.data == 'to_start_one_link_stat':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    dirty_link: str = update.message.text
    if decoded_link := LinkValidator.validate(dirty_link, scopes=ValidationScopes.TIKTOK_USER_ONE_VIDEO):
        parse_tt_one_video.apply_async(args=[decoded_link, update.effective_chat.id])
        message = MessageContainer.parsing_success
    else:
        message = MessageContainer.link_validation_error.format(link=dirty_link)

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
    )
    await asyncio.sleep(1)
    # возвращает редирект на welcome_handler
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.ONE_LINK_PARSING)


async def command_parse_by_sec_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отдельный хендлер на команду с префиксом !by_id"""
    await check_bot_context(update, context)
    sec_uid = update.message.text.split(' ')[-1]
    parse_tiktok_by_sec_uid.apply_async(args=[sec_uid, update.effective_chat.id])
    await context.bot.send_message(
        update.effective_chat.id,
        text=MessageContainer.parsing_by_sec_uid,
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.PARSING)
