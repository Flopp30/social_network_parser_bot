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
    ContextTypes,
)

from bot_parts.helpers import check_bot_context
from bot_parts.keyboards import START_BOARD
from bot_parts.validators import LinkValidator
from parserbot.tasks import parse_tiktok

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
    await check_bot_context(update, context)
    message = (
        "Отправь ссылку для парсинга\n"
        "Умею: tik-tok (user, music).\n"
        "Чтобы избежать проблем:\n"
        "   - Ссылка должны быть максимально чистой.\n"
        "   - Не надо кидать ссылки не на тот ресурс, пожалуйста.\n"
        "Примеры:\n<code>https://www.tiktok.com/@domixx007</code> \n\n"
        "<code>https://www.tiktok.com/music/Scary-Garry-6914598970259490818</code>\n\n"
        "Я оконечно обложил все валидацией, но давайте не будем испытывать судьбу 😉"
    )
    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
        parse_mode='HTML',
    )
    return "AWAIT_LINK_TO_PARSE"


async def parser_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    if (decoded_link := LinkValidator.validate(update.message.text)):
        message = ("Ссылка прошла валидацию, приступил к парсингу, ожидайте.\n "
                   "Средняя скорость:\n"
                   "    - Музыка: 150-200 видео/сек\n"
                   "    - Юзер: 20-30 видео/сек.\n"
                   "Бот в любом случае вернет какой-то ответ. "
                   "Во избежании всяких блокировок - не надо одну и ту же ссылку "
                   "отправлять несколько раз до ответа 🙄")
        parse_tiktok.apply_async(args=[decoded_link, update.effective_chat.id])
        await asyncio.sleep(5)
    else:
        message = 'Ссылка не валидна. Если вы считаете, что это не так - стукните в лс @Flopp'
    await context.bot.send_message(
        update.effective_chat.id,
        text=message
    )
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


def main():
    import tracemalloc
    tracemalloc.start()
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(settings.BOT_LOG_LEVEL)
    logger.addHandler(stream_handler)

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

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
