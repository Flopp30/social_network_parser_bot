from typing import Literal

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot_parts.helpers import WelcomeRedirectType, check_bot_context
from bot_parts.keyboards import MONITORING_BOARD, ONE_LINK_BOARD, PARSING_BOARD, START_BOARD, GEO_PARSING_BOARD
from bot_parts.messages import MessageContainer


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start handler"""

    # принудительно обновляем пользователя
    await check_bot_context(update, context, force_update=True)
    # проверяем, подтвержден ли он
    if context.user_data['user'].is_approved:
        message = MessageContainer.start_approved
        keyboard = START_BOARD
        state = 'AWAIT_WELCOME_CHOICE'
    else:
        message = MessageContainer.start_not_approved
        keyboard = None
        state = 'START'

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=keyboard,
    )
    return state


async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    """Ловит callback с START_BOARD"""
    default_state: str = 'AWAIT_WELCOME_CHOICE'
    redirect_callback: Literal['monitoring', 'parsing', 'geo_parsing', 'one_link_stat'] | None = kwargs.get('redirect_callback')

    # либо редирект, либо callback с кнопки
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

    # geo_parsing
    elif redirect_callback == WelcomeRedirectType.GEO_PARSING:
        message = MessageContainer.geo_parsing_welcome
        keyboard = GEO_PARSING_BOARD
        state = 'AWAIT_LINK_TO_PARSING_WITH_GEO'

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
