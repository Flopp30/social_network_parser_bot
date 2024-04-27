import asyncio
import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes, PrefixHandler,
)

from bot_parts.helpers import check_bot_context
from bot_parts.keyboards import START_BOARD
from common.validators import LinkValidator
from parserbot.tasks import parse_tiktok, parse_tiktok_by_sec_uid, parse_yt_music_link

logger = logging.getLogger('tbot')
job_queue = None


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context, force_update=True)
    if context.user_data['user'].is_approved:
        message = (
            'О, ты получил подтверждение. Ну тогда давай приступим!'
        )
        keyboard = START_BOARD
        STATE = "AWAIT_WELCOME_CHOICE"
    else:
        message = (
            'Привет, это Social Networks Bot. Для получения доступа обратитесь к @Afremovv'
        )
        keyboard = None
        STATE = "START"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard,
    )
    context.user_data['user'].state = 'START'
    return STATE


async def parser_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    if update.callback_query or kwargs.get('redirect'):
        await check_bot_context(update, context)
        message = (
            "Отправь ссылку для парсинга\n"
            "Умею:\n"
            "   - Tik-tok: user, music.\n"
            "   - Youtube: music.\n"
            "Примеры:\n<code>https://www.tiktok.com/@domixx007</code> \n\n"
            "<code>https://www.tiktok.com/music/Scary-Garry-6914598970259490818</code>\n\n"
            "<code>https://www.youtube.com/source/ZmKk4krdy84/shorts</code>\n\n"
        )
        await context.bot.send_message(
            update.effective_chat.id,
            text=message,
            parse_mode='HTML',
        )
        return "AWAIT_LINK_TO_PARSE"
    return "AWAIT_WELCOME_CHOICE"


async def parser_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)

    if decoded_link := LinkValidator.validate(update.message.text):
        message = "Ссылка прошла валидацию, задача на парсинг поставлена.\n "
        if 'tiktok' in decoded_link:
            parse_tiktok.apply_async(args=[decoded_link, update.effective_chat.id])
        elif 'youtube' in decoded_link:
            parse_yt_music_link.apply_async(args=[decoded_link, update.effective_chat.id])
    elif update.message.text.startswith('MS'):
        parse_tiktok_by_sec_uid.apply_async(args=[update.message.text.strip(), update.effective_chat.id])
        message = f'Запущен парсинг по ID: {update.message.text}'
    else:
        message = 'Ссылка не валидна. Если вы считаете, что это не так - стукните в лс @Flopp'

    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
    await asyncio.sleep(1)
    return await parser_welcome_handler(update, context, redirect=True)


async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    if update.message:
        user_reply = update.message.text
    elif update.callback_query.data:
        user_reply = update.callback_query.data
    else:
        return
    if not context.user_data['user'].is_approved:
        user_state = context.user_data['user'].state = 'START'
    elif user_reply == '/start':
        user_state = context.user_data['user'].state = 'START'
    else:
        user_state = context.user_data['user'].state or 'START'
    states_function = {
        'START': start,
        'NEW': start,
        "AWAIT_WELCOME_CHOICE": parser_welcome_handler,
        "AWAIT_LINK_TO_PARSE": parser_start_handler,
    }

    state_handler = states_function[user_state]
    next_state = await state_handler(update, context)
    context.user_data['user'].state = next_state
    await context.user_data['user'].asave()


async def parse_by_sec_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    sec_uid = update.message.text.split(' ')[-1]
    parse_tiktok_by_sec_uid.apply_async(args=[sec_uid, update.effective_chat.id])
    message = f'Парсинг по {sec_uid} запущен.'
    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
    return await parser_welcome_handler(update, context, redirect=True)


def main():
    import tracemalloc
    tracemalloc.start()
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(settings.BOT_LOG_LEVEL)
    logger.addHandler(stream_handler)

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    application.add_handler(PrefixHandler('!', ['by_id'], parse_by_sec_uid))
    application.add_handler(CommandHandler('start', user_input_handler))
    application.add_handler(CallbackQueryHandler(user_input_handler))
    application.add_handler(MessageHandler(filters.TEXT, user_input_handler))

    try:
        if settings.BOT_MODE == 'webhook':
            logger.warning('Bot started in WEBHOOK mode')
            application.run_webhook(
                listen="0.0.0.0",
                port=5000,
                url_path=settings.TELEGRAM_TOKEN,
                webhook_url=f"{settings.WEBHOOK_URL}{settings.TELEGRAM_TOKEN}"
            )
        else:
            logger.warning('Bot started in POLLING mode')
            application.run_polling()
    except Exception:
        import traceback
        logger.warning(traceback.format_exc())
