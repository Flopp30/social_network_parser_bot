from telegram import InlineKeyboardMarkup, InlineKeyboardButton

START_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Парсинг', callback_data='parsing')],
        [InlineKeyboardButton('Статистика для одной ссылки', callback_data='one_link_stat')],
        [InlineKeyboardButton('Мониторинг', callback_data='monitoring')],
    ]
)

PARSING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_from_parsing')],
    ]
)

ONE_LINK_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_one_link_stat')],
    ]
)

MONITORING_BOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('Назад', callback_data='to_start_from_monitoring')],
        [InlineKeyboardButton('Добавить ссылку для отслеживания', callback_data='add_link')],
        [InlineKeyboardButton('Получить список отслеживаемых ссылок', callback_data='get_list')],
        [InlineKeyboardButton('Прекратить отслеживание ссылки', callback_data='remove_link')],
    ]
)
