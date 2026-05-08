from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


CONTENT_TYPE_LABELS = {
    "anime": "🎌 Аниме",
    "movie": "🎬 Фильм / Мультик",
    "series": "📺 Сериал",
    "game": "🎮 Игра",
    "book": "📚 Книга",
}


def community_hub_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    inline_keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Предложить контент",
                callback_data="community_suggest_start",
            )
        ],
        [
            InlineKeyboardButton(
                text="🎁 Запросить Premium",
                callback_data="community_request_premium",
            )
        ],
    ]

    if is_admin:
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="📝 Заявки",
                    callback_data="community_admin_suggestions",
                ),
                InlineKeyboardButton(
                    text="📊 Авторы",
                    callback_data="community_admin_contributors",
                ),
            ]
        )
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="📥 Черновики",
                    callback_data="community_admin_drafts",
                )
            ]
        )
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    text="💎 Reward-запросы",
                    callback_data="community_admin_reward_requests",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def community_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text=label,
                callback_data=f"community_type:{content_type}",
            )
        ]
        for content_type, label in CONTENT_TYPE_LABELS.items()
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="community_hub",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
