from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def bottom_nav_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏠 Меню"),
                KeyboardButton(text="🫶 Внести в базу"),
            ],
            [
                KeyboardButton(text="⭐ Избранное"),
                KeyboardButton(text="💎 Premium"),
            ],
        ],
        is_persistent=True,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выбери раздел",
    )
