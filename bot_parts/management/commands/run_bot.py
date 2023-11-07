import logging
from datetime import timedelta

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
    PrefixHandler
)

from bot_parts.helpers import check_bot_context

logger = logging.getLogger('tbot')


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context, force_update=True)
    message = (
        'Привет, это парсер бот.'
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
    )
    context.user_data['user'].state = 'START'
    return 'START'


async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_bot_context(update, context)
    user_state = context.user_data['user'].state or 'START'
    states_function = {
        'START': start,
        'NEW': start,
    }

    state_handler = states_function[user_state]
    next_state = await state_handler(update, context)
    context.user_data['user'].state = next_state
    await context.user_data['user'].asave()


def main():
    import tracemalloc
    tracemalloc.start()
    # logger
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(settings.BOT_LOG_LEVEL)
    logger.addHandler(stream_handler)

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

    # periodic tasks | may be required in the future
    # job_queue = application.job_queue
    # job_queue.run_repeating(
    #     reload_in_memory_data,
    #     interval=timedelta(minutes=10),
    #     first=1
    # )

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
