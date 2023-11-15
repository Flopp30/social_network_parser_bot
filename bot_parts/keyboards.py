from telegram import InlineKeyboardMarkup, InlineKeyboardButton

START_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Начать!', callback_data='start')]
    ]
)
