from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def tags_keyboard(vibes: dict):
    keyboard = []

    for tag, label in vibes.items():
        keyboard.append([
            InlineKeyboardButton(
                text=label,
                callback_data=f"tag:{tag}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="✅ Сохранить",
            callback_data="save_content"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
