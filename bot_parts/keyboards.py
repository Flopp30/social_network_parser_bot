from telegram import InlineKeyboardMarkup, InlineKeyboardButton

START_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Парсинг', callback_data='parsing')],
        [InlineKeyboardButton('Мониторинг', callback_data='monitoring')],
    ]
)

PARSING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start')],
    ]
)

MONITORING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start')],
        [InlineKeyboardButton('Добавить ссылку для отслеживания', callback_data='add_link')],
        [InlineKeyboardButton('Получить список отслеживаемых ссылок', callback_data='get_list')],
        [InlineKeyboardButton('Прекратить отслеживание ссылки', callback_data='remove_link')],
    ]
)
