from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config_baze.admins import ADMINS
from utils.analytics import (
    get_analytics_summary,
    get_content_shown_by_type,
    get_event_counts,
    get_top_content,
    get_top_sources,
)

router = Router()

CONTENT_TYPE_LABELS = {
    "anime": "🎌 Аниме",
    "book": "📚 Книги",
    "game": "🎮 Игры",
    "movie": "🎬 Фильмы",
    "series": "📺 Сериалы",
}

EVENT_LABELS = {
    "start": "Старт бота",
    "main_menu": "Главное меню",
    "open_content_hub": "Подбор контента",
    "premium_opened": "Открыли Premium",
    "premium_buy_clicked": "Нажали покупку",
    "premium_paid": "Оплатили Premium",
    "favorite_added": "Добавили в избранное",
    "favorite_removed": "Убрали из избранного",
    "rating_up": "🔥 Наш слон",
    "rating_down": "❄️ Не наш",
    "rating_base": "🎓 БАЗА одобряет",
    "content_shown": "Показано карточек",
    "content_added": "Админ добавил контент",
}


def label_event(event_name: str) -> str:
    return EVENT_LABELS.get(event_name, event_name)


def label_content_type(content_type: str | None) -> str:
    return CONTENT_TYPE_LABELS.get(content_type or "", content_type or "без типа")


def format_rows(rows, formatter, empty_text: str = "пока пусто") -> str:
    if not rows:
        return empty_text
    return "\n".join(formatter(row) for row in rows)


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id not in ADMINS:
        return

    summary = get_analytics_summary()
    event_counts = get_event_counts(days=7)
    shown_by_type = get_content_shown_by_type(days=7)
    top_content = get_top_content(days=7)
    top_sources = get_top_sources(days=7)

    text = "\n".join([
        "📊 <b>Статистика БАЗЫ №600</b>",
        "",
        "<b>Пользователи</b>",
        f"Всего: <b>{summary['users_total']}</b>",
        f"Новые за 24ч: <b>{summary['users_24h']}</b>",
        f"Новые за 7д: <b>{summary['users_7d']}</b>",
        f"Premium сейчас: <b>{summary['premium_total']}</b>",
        "",
        "<b>Активность</b>",
        f"Активных за 24ч: <b>{summary['active_users_24h']}</b>",
        f"Активных за 7д: <b>{summary['active_users_7d']}</b>",
        f"Событий за 24ч: <b>{summary['events_24h']}</b>",
        f"Событий за 7д: <b>{summary['events_7d']}</b>",
        "",
        "<b>События за 7д</b>",
        format_rows(
            event_counts,
            lambda row: f"• {label_event(row[0])}: <b>{row[1]}</b>",
        ),
        "",
        "<b>Показы по разделам за 7д</b>",
        format_rows(
            shown_by_type,
            lambda row: f"• {label_content_type(row[0])}: <b>{row[1]}</b>",
        ),
        "",
        "<b>Топ источников за 7д</b>",
        format_rows(
            top_sources,
            lambda row: f"• {row[0]}: <b>{row[1]}</b>",
        ),
        "",
        "<b>Топ карточек за 7д</b>",
        format_rows(
            top_content,
            lambda row: f"• {label_content_type(row[0])}: {row[1]} — <b>{row[2]}</b>",
        ),
    ])

    await message.answer(text, parse_mode="HTML")
