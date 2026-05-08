from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def content_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎌 Аниме", callback_data="admin_type:anime")],
        [InlineKeyboardButton(text="🎬 Фильм", callback_data="admin_type:movie")],
        [InlineKeyboardButton(text="📺 Сериал", callback_data="admin_type:series")],
        [InlineKeyboardButton(text="🎮 Игра", callback_data="admin_type:game")],
        [InlineKeyboardButton(text="📚 Книга", callback_data="admin_type:book")]
    ])
