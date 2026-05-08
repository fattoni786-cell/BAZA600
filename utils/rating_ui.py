from aiogram.types import CopyTextButton, InlineKeyboardButton

RATING_UP = 1
RATING_DOWN = -1
RATING_BASE_APPROVES = 2


def build_rating_rows(
    user_rating: int | None = None,
    is_premium: bool = False,
) -> list[list[InlineKeyboardButton]]:
    rows = [
        [
            InlineKeyboardButton(
                text="🔥 Наш слон" + (" ✅" if user_rating == RATING_UP else ""),
                callback_data="rate:up",
            ),
            InlineKeyboardButton(
                text="❄️ Не наш" + (" ✅" if user_rating == RATING_DOWN else ""),
                callback_data="rate:down",
            ),
        ]
    ]

    if is_premium:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🎓 БАЗА одобряет"
                    + (" ✅" if user_rating == RATING_BASE_APPROVES else ""),
                    callback_data="rate:base",
                ),
            ]
        )

    return rows


def build_copy_title_row(title: str | None) -> list[InlineKeyboardButton]:
    if not title:
        return []

    return [
        InlineKeyboardButton(
            text="📋 Скопировать название",
            copy_text=CopyTextButton(text=title),
        )
    ]


def build_card_nav_row(show_more: bool = False) -> list[InlineKeyboardButton]:
    row = [
        InlineKeyboardButton(text="💬 Реакции", callback_data="card_reactions"),
    ]
    if show_more:
        row.append(InlineKeyboardButton(text="⋯ Ещё", callback_data="card_more"))
    return row


def build_card_back_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="⬅️ Назад", callback_data="card_back")]
