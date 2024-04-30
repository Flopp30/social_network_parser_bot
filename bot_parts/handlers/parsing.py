import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from bot_parts.helpers import check_bot_context, WelcomeRedirectType
from bot_parts.messages import MESSAGE_MAP
from common.validators import LinkValidator
from parserbot.tasks import parse_tiktok, parse_tiktok_by_sec_uid, parse_yt_music_link
from bot_parts.handlers.start import welcome_handler, start_handler


async def add_link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запускает задачу на парсинг ссылки | id (для тиктока)"""
    await check_bot_context(update, context)

    # редирект назад
    if update.callback_query and update.callback_query.data == 'to_start':
        context.user_data['user'].state = 'START'
        return await start_handler(update, context)

    if decoded_link := LinkValidator.validate(update.message.text):
        if 'tiktok' in decoded_link:
            parse_tiktok.apply_async(args=[decoded_link, update.effective_chat.id])
        elif 'youtube' in decoded_link:
            parse_yt_music_link.apply_async(args=[decoded_link, update.effective_chat.id])
        message = MESSAGE_MAP['parsing_success']
    elif update.message.text.startswith('MS'):
        # парсинг по sec_uid (для тиктока)
        parse_tiktok_by_sec_uid.apply_async(args=[update.message.text.strip(), update.effective_chat.id])
        message = MESSAGE_MAP['parsing_by_sec_uid']
    else:
        message = MESSAGE_MAP['link_validation_error']

    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
    await asyncio.sleep(1)
    # возвращает редирект на welcome_handler
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.PARSING)


async def command_parse_by_sec_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отдельный хендлер на команду с префиксом !by_id"""
    await check_bot_context(update, context)
    sec_uid = update.message.text.split(' ')[-1]
    parse_tiktok_by_sec_uid.apply_async(args=[sec_uid, update.effective_chat.id])
    await context.bot.send_message(
        update.effective_chat.id,
        text=MESSAGE_MAP['parsing_by_sec_uid']
    )
    return await welcome_handler(update, context, redirect_callback=WelcomeRedirectType.PARSING)
