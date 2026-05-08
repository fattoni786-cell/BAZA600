from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def movies_mode_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстро по вайбу", callback_data="movies_fast")],
            [InlineKeyboardButton(text="🦉 Удиви меня", callback_data="movies_surprise")],
            [InlineKeyboardButton(text="🧠 Персонально", callback_data="movies_personal")],
            [InlineKeyboardButton(text="💎 Premium-подборки", callback_data="movies_collections")],
        ]
    )
