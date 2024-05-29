from typing import Literal

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot_parts.helpers import check_bot_context, WelcomeRedirectType
from bot_parts.keyboards import START_BOARD, MONITORING_BOARD, PARSING_BOARD, ONE_LINK_BOARD
from bot_parts.messages import MessageContainer


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start handler"""

    # принудительно обновляем пользователя
    await check_bot_context(update, context, force_update=True)
    # проверяем, подтвержден ли он
    if context.user_data['user'].is_approved:
        message = MessageContainer.start_approved
        keyboard = START_BOARD
        state = "AWAIT_WELCOME_CHOICE"
    else:
        message = MessageContainer.start_not_approved
        keyboard = None
        state = "START"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard,
    )
    return state


async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    """Ловит callback с START_BOARD"""
    default_state: str = 'AWAIT_WELCOME_CHOICE'
    redirect_callback: Literal['monitoring', 'parsing', 'one_link_stat'] | None = kwargs.get('redirect_callback')

    # либо редирект, либо callback с кнопки, иначе просто state возвращаем
    if not redirect_callback and not update.callback_query:
        return default_state

    # кейс, когда пришел обычный callback
    if not redirect_callback:
        redirect_callback = update.callback_query.data

    keyboard: InlineKeyboardMarkup | None
    state: str
    # parsing button
    if redirect_callback == WelcomeRedirectType.PARSING:
        message = MessageContainer.parsing_welcome
        keyboard = PARSING_BOARD
        state = 'AWAIT_LINK_TO_PARSE'

    # one link stat button
    elif redirect_callback == WelcomeRedirectType.ONE_LINK_PARSING:
        message = MessageContainer.one_link_stat_welcome
        keyboard = ONE_LINK_BOARD
        state = 'AWAIT_LINK_TO_GET_STAT'

    # monitoring button
    else:
        message = MessageContainer.monitoring_welcome
        keyboard = MONITORING_BOARD
        state = 'AWAIT_MONITORING_CHOICE'

    await context.bot.send_message(
        update.effective_chat.id,
        text=message,
        parse_mode='HTML',
        reply_markup=keyboard,
    )
    return state
