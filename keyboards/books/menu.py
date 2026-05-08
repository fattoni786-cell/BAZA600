from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def books_mode_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Быстро по вайбу", callback_data="books_fast")],
            [InlineKeyboardButton(text="🦉 Удиви меня", callback_data="books_surprise")],
            [InlineKeyboardButton(text="🧠 Персонально", callback_data="books_personal")],
            [InlineKeyboardButton(text="💎 Premium-подборки", callback_data="books_collections")],
        ]
    )
