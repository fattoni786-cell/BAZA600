from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def premium_collections_keyboard(
    options: list[str],
    pick_prefix: str,
    refresh_callback: str,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=option,
                callback_data=f"{pick_prefix}:{idx}",
            )
        ]
        for idx, option in enumerate(options)
    ]

    keyboard.append(
        [InlineKeyboardButton(text="🔄 Обновить подборки", callback_data=refresh_callback)]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
