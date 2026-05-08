from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.anime.personal import personal_anime_keyboard
from keyboards.anime.vibes import another_anime_keyboard
from keyboards.books.personal import personal_book_keyboard
from keyboards.books.vibes import another_book_keyboard
from keyboards.games.personal import personal_game_keyboard
from keyboards.games.vibes import another_game_keyboard
from keyboards.movies.personal import personal_movie_keyboard
from keyboards.movies.vibes import another_movie_keyboard
from keyboards.series.personal import personal_series_keyboard
from keyboards.series.vibes import another_series_keyboard
from utils.access import has_premium_access
from utils.analytics import track_event
from utils.card_keyboard import build_current_card_keyboard
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_rating, set_rating
from utils.fast_vibes import has_more_in_fast_vibe
from utils.media_sender import build_caption
from utils.premium_collections import has_more_in_collection
from utils.rating_ui import (
    RATING_BASE_APPROVES,
    RATING_DOWN,
    RATING_UP,
)

router = Router()

RATING_ACTIONS = {
    "up": (RATING_UP, "🔥 Наш слон!"),
    "down": (RATING_DOWN, "❄️ Не наш"),
    "base": (RATING_BASE_APPROVES, "🎓 БАЗА одобряет"),
}


@router.callback_query(F.data.in_({"card_reactions", "card_more", "card_back"}))
async def switch_card_panel(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    view_by_action = {
        "card_reactions": "reactions",
        "card_more": "more",
        "card_back": "main",
    }
    keyboard = build_current_card_keyboard(
        data=data,
        user=user,
        view=view_by_action[callback.data],
    )

    if not keyboard:
        await callback.answer("Карточка уже закрыта", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("rate:"))
async def rate_content(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
):
    action = callback.data.split(":", 1)[1]
    mapping = RATING_ACTIONS.get(action)

    if not mapping:
        await callback.answer("Оценка не найдена", show_alert=True)
        return

    if action == "base" and not has_premium_access(user):
        await callback.answer("Эта реакция доступна только в Premium", show_alert=True)
        return

    value, toast = mapping

    data = await state.get_data()
    item = data.get("current_item")
    content_type = data.get("current_type")
    vibe = data.get("current_vibe")
    current_source = data.get("current_source")
    extra_text = data.get("current_caption_extra")
    collection_name = data.get("current_collection_name")

    if not item or not content_type:
        await callback.answer("Контент не найден", show_alert=True)
        return

    user_id = user["telegram_id"]
    content_id = item["title"]

    set_rating(
        user_id=user_id,
        content_type=content_type,
        content_id=content_id,
        value=value,
    )
    track_event(
        user_id,
        f"rating_{action}",
        content_type=content_type,
        content_id=content_id,
        source=current_source,
        metadata={"vibe": vibe, "collection_name": collection_name},
    )

    keyboard = build_current_card_keyboard(
        data=data,
        user=user,
        view="reactions",
        user_rating=get_user_rating(user_id, content_type, content_id),
    )
    if not keyboard:
        await callback.answer("Неизвестный тип", show_alert=True)
        return

    caption = build_caption(
        content_type=content_type,
        item=item,
        extra_text=extra_text,
        context_note=f"💎 Подборка: <b>{collection_name}</b>" if collection_name and current_source and current_source.endswith("_collection") else None,
    )

    if callback.message.caption:
        await callback.message.edit_caption(
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            caption,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await callback.answer(toast)
