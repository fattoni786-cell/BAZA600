from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def movie_vibe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="😔 Грустно. Хочется мотивации",
                callback_data="movie_vibe_sad_motivation"
            )
        ],
        [
            InlineKeyboardButton(
                text="💥 Экшен",
                callback_data="movie_vibe_action"
            )
        ]
    ])

def another_movie_keyboard(vibe: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎲 Не зашёл. Давай другой",
                callback_data=f"another_movie:{vibe}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🏠 В главное меню",
                callback_data="go_to_menu"
            )
        ]
    ])
