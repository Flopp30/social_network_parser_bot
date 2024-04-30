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
import bot_parts.handlers.parsing as parsing_handlers
import bot_parts.handlers.monitoring as monitoring_handlers
import bot_parts.handlers.start as start_handlers
from bot_parts.helpers import check_bot_context

logger = logging.getLogger('tbot')


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()


async def user_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает входящие сообщения от пользователей"""
    await check_bot_context(update, context)
    # получаем тело сообщения
    if update.message:
        # обычное сообщение
        user_reply = update.message.text
    elif update.callback_query.data:
        # callback
        user_reply = update.callback_query.data
    else:
        return

    if not context.user_data['user'].is_approved or user_reply == '/start':
        user_state = context.user_data['user'].state = 'START'
    else:
        user_state = context.user_data['user'].state or 'START'

    # мапа, возвращающая callback функции для вызова дальше.
    states_function = {
        # start
        'START': start_handlers.start_handler,
        'NEW': start_handlers.start_handler,
        "AWAIT_WELCOME_CHOICE": start_handlers.welcome_handler,
        # парсинг
        "AWAIT_LINK_TO_PARSE": parsing_handlers.add_link_handler,
        # мониторинг
        'AWAIT_MONITORING_CHOICE': monitoring_handlers.monitoring_choice_handler,
        'MONITORING_AWAIT_LINK_FOR_ADDING': monitoring_handlers.add_link_handler,
        'MONITORING_AWAIT_ID_FOR_DELETING': monitoring_handlers.remove_link_handler,
    }
    # вызываем функцию для получения state
    state_handler = states_function[user_state]
    # получаем некст state
    next_state = await state_handler(update, context)
    # записываем следующий state в юзера
    context.user_data['user'].state = next_state
    await context.user_data['user'].asave()


def main():
    import tracemalloc
    tracemalloc.start()
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(settings.BOT_LOG_LEVEL)
    logger.addHandler(stream_handler)

    application = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    # добавляем обработчики
    # сначала команду, чтобы она не попала в общий поток user_input_handler
    application.add_handler(PrefixHandler('!', ['by_id'], parsing_handlers.command_parse_by_sec_uid))
    # сюда все сообщения, т.к. команда /start, callback'и и текст
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
