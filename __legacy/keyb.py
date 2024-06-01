from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def uniKeyb(buttons):
    if buttons is None: return None
    kb = InlineKeyboardMarkup(row_width=10)
    for row in buttons:
        butt = [InlineKeyboardButton(f"{b[0]}", callback_data=f"{b[1]}") for b in row]
        kb.add(*butt)
    return kbroot
