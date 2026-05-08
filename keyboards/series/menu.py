from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def series_mode_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстро по вайбу", callback_data="series_fast")],
            [InlineKeyboardButton(text="🦉 Удиви меня", callback_data="series_surprise")],
            [InlineKeyboardButton(text="🧠 Персонально", callback_data="series_personal")],
            [InlineKeyboardButton(text="💎 Premium-подборки", callback_data="series_collections")],
        ]
    )
