from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from data.games import GAME_PLATFORMS, get_game_platform_label


def game_platform_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    keyboard = []

    for platform in GAME_PLATFORMS:
        marker = "✅" if platform in selected else "⬜️"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{marker} {get_game_platform_label(platform)}",
                    callback_data=f"toggle_game_platform:{platform}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="💾 Сохранить платформы", callback_data="save_game_platforms")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
