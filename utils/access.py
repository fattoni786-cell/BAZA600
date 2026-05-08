from datetime import datetime, timedelta

from utils.db import (
    get_free_favorites_export_last_used,
    get_free_personal_last_used,
    get_user_favorites,
    set_free_favorites_export_last_used,
    set_free_personal_last_used,
)
from utils.users import is_premium

FREE_FAVORITES_LIMIT = 3
FREE_PERSONAL_COOLDOWN_HOURS = 24
FREE_FAVORITES_EXPORT_COOLDOWN_DAYS = 7


def favorites_limit(user: dict) -> int | None:
    if is_premium(user):
        return None
    return FREE_FAVORITES_LIMIT


def can_add_to_favorites(user: dict) -> tuple[bool, int | None]:
    limit = favorites_limit(user)

    if limit is None:
        return True, None

    current_count = len(get_user_favorites(user["telegram_id"]))
    return current_count < limit, limit


def has_premium_access(user: dict) -> bool:
    return is_premium(user)


def premium_status_text(user: dict) -> str:
    if not has_premium_access(user):
        return "🤗 Статус: <b>Free</b>"

    premium_until = user.get("premium_until")

    if not premium_until:
        return "💎 Статус: <b>Premium</b>"

    try:
        expires_at = datetime.fromisoformat(premium_until)
        formatted = expires_at.strftime("%d.%m.%Y")
        return f"💎 Статус: <b>Premium</b> до {formatted}"
    except ValueError:
        return "💎 Статус: <b>Premium</b>"


def premium_feature_locked_text(feature_name: str) -> str:
    return (
        f"💎 <b>{feature_name}</b> доступно только в Premium.\n\n"
        "Что дает Premium:\n"
        "• персональный подбор\n"
        "• premium-подборки\n"
        "• безлимитное избранное\n\n"
        "Открыть экран Premium можно кнопкой ниже."
    )


def free_personal_status(user: dict) -> tuple[bool, datetime | None]:
    if has_premium_access(user):
        return True, None

    last_used_at = get_free_personal_last_used(user["telegram_id"])
    if not last_used_at:
        return True, None

    try:
        last_used = datetime.fromisoformat(last_used_at)
    except ValueError:
        return True, None

    next_available_at = last_used + timedelta(hours=FREE_PERSONAL_COOLDOWN_HOURS)
    if datetime.utcnow() >= next_available_at:
        return True, None

    return False, next_available_at


def consume_free_personal_use(user_id: int):
    set_free_personal_last_used(user_id, datetime.utcnow().isoformat())


def free_personal_locked_text(feature_name: str, next_available_at: datetime) -> str:
    formatted = next_available_at.strftime("%d.%m %H:%M")
    return (
        f"🤗 <b>{feature_name}</b> для Free доступен <b>1 раз в 24 часа</b>.\n\n"
        f"Следующий персональный подбор откроется после <b>{formatted}</b>.\n\n"
        "Premium снимает это ограничение и даёт безлимитный персональный подбор."
    )


def free_favorites_export_status(user: dict) -> tuple[bool, datetime | None]:
    if has_premium_access(user):
        return True, None

    last_used_at = get_free_favorites_export_last_used(user["telegram_id"])
    if not last_used_at:
        return True, None

    try:
        last_used = datetime.fromisoformat(last_used_at)
    except ValueError:
        return True, None

    next_available_at = last_used + timedelta(days=FREE_FAVORITES_EXPORT_COOLDOWN_DAYS)
    if datetime.utcnow() >= next_available_at:
        return True, None

    return False, next_available_at


def consume_free_favorites_export_use(user_id: int):
    set_free_favorites_export_last_used(user_id, datetime.utcnow().isoformat())


def free_favorites_export_locked_text(next_available_at: datetime) -> str:
    formatted = next_available_at.strftime("%d.%m %H:%M")
    return (
        "🤗 Экспорт избранного для Free доступен <b>1 раз в 7 дней</b>.\n\n"
        f"Следующий экспорт откроется после <b>{formatted}</b>.\n\n"
        "Premium снимает это ограничение и даёт экспорт без лимита."
    )
