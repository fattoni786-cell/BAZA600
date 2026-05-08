from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from data.games import GAME_PLATFORMS, get_game_platform_label


def game_platforms_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for platform in GAME_PLATFORMS:
        marker = "✅" if platform in selected else "⬜️"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{marker} {get_game_platform_label(platform)}",
                    callback_data=f"admin_game_platform_toggle:{platform}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="➡️ Дальше к premium-подборкам",
                callback_data="admin_game_platforms_done",
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
