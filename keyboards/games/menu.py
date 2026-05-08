from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def games_mode_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстро по вайбу", callback_data="games_fast")],
            [InlineKeyboardButton(text="🦉 Удиви меня", callback_data="games_surprise")],
            [InlineKeyboardButton(text="🧠 Персонально", callback_data="games_personal")],
            [InlineKeyboardButton(text="💎 Premium-подборки", callback_data="games_collections")],
            [InlineKeyboardButton(text="🕹 Мои платформы", callback_data="games_platforms")],
        ]
    )
