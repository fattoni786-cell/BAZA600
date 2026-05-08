from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils.rating_ui import build_card_back_row, build_card_nav_row, build_copy_title_row, build_rating_rows


def game_personal_prompt_keyboard() -> None:
    return None


def game_personal_question_keyboard(
    answers: list[str],
    current_index: int,
    total: int,
) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=answer_text,
                callback_data=f"game_personal_answer:{idx}",
            )
        ]
        for idx, answer_text in enumerate(answers)
    ]

    keyboard.append(
        [
            InlineKeyboardButton(
                text=f"🎮 Вопрос {current_index + 1} из {total}",
                callback_data="game_personal_progress",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def personal_game_keyboard(
    has_backup: bool,
    title: str | None = None,
    is_favorite: bool = False,
    user_rating: int | None = None,
    is_premium: bool = False,
    view: str = "main",
) -> InlineKeyboardMarkup:
    keyboard = []

    if view == "reactions":
        keyboard.extend(build_rating_rows(user_rating=user_rating, is_premium=is_premium))
        keyboard.append(build_card_back_row())
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    copy_row = build_copy_title_row(title)
    if copy_row:
        keyboard.append(copy_row)

    if has_backup:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🎲 Запасной вариант",
                    callback_data="game_personal_backup",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                text="❌ Убрать из избранного" if is_favorite else "⭐ В избранное",
                callback_data="toggle_favorite",
            )
        ]
    )
    keyboard.append(build_card_nav_row())
    keyboard.append(
        [InlineKeyboardButton(text="🧠 Новый персональный подбор", callback_data="games_personal")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
