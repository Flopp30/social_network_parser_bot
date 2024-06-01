from telegram import InlineKeyboardButton, InlineKeyboardMarkup

START_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Парсинг', callback_data='parsing')],
        [InlineKeyboardButton('Парсинг с гео', callback_data='geo_parsing')],
        [InlineKeyboardButton('Статистика для одной ссылки', callback_data='one_link_stat')],
        [InlineKeyboardButton('Мониторинг', callback_data='monitoring')],
    ],
)

PARSING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_from_parsing')],
    ],
)

GEO_PARSING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_from_geo_parsing')],
    ],
)

ONE_LINK_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_one_link_stat')],
    ],
)

MONITORING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_from_monitoring')],
        [InlineKeyboardButton('Добавить ссылку для отслеживания', callback_data='add_link')],
        [InlineKeyboardButton('Получить список отслеживаемых ссылок', callback_data='get_list')],
        [InlineKeyboardButton('Прекратить отслеживание ссылки', callback_data='remove_link')],
    ],
)
