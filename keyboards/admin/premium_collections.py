from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def premium_collections_keyboard(
    options: list[str],
    selected: list[str],
    premium_only: bool = False,
) -> InlineKeyboardMarkup:
    keyboard = []

    for idx, name in enumerate(options):
        marker = "✅" if name in selected else "▫️"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{marker} {name}",
                    callback_data=f"admin_collection_toggle:{idx}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text=(
                    "🔒 Только для premium-подборок: ВКЛ"
                    if premium_only
                    else "🌍 Доступно и в общей выдаче"
                ),
                callback_data="admin_collection_only_toggle",
            )
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="➡️ Дальше к тегам",
                callback_data="admin_collections_done",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
