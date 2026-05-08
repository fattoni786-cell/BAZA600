from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def anime_mode_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстро по вайбу", callback_data="anime_fast")],
            [InlineKeyboardButton(text="🦉 Удиви меня", callback_data="anime_surprise")],
            [InlineKeyboardButton(text="🧠 Персонально", callback_data="anime_personal")],
            [InlineKeyboardButton(text="💎 Premium-подборки", callback_data="anime_collections")],
        ]
    )
