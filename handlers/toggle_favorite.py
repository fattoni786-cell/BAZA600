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
from utils.access import can_add_to_favorites, has_premium_access
from utils.analytics import track_event
from utils.card_keyboard import build_current_card_keyboard
from utils.content_history import get_recently_seen_titles
from utils.db import (
    add_to_favorites,
    get_user_rating,
    is_in_favorites,
    remove_from_favorites,
)
from utils.fast_vibes import has_more_in_fast_vibe
from utils.premium_collections import has_more_in_collection

router = Router()


@router.callback_query(F.data == "toggle_favorite")
async def toggle_favorite(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
):
    data = await state.get_data()

    item = data.get("current_item")
    content_type = data.get("current_type")
    vibe = data.get("current_vibe")
    current_source = data.get("current_source")
    collection_name = data.get("current_collection_name")

    if not item or not content_type:
        await callback.answer("Не удалось определить объект", show_alert=True)
        return

    user_id = user["telegram_id"]
    content_id = item.get("title")

    if not content_id:
        await callback.answer("Ошибка данных", show_alert=True)
        return

    if is_in_favorites(user_id, content_type, content_id):
        remove_from_favorites(user_id, content_type, content_id)
        is_fav = False
        action_text = "Убрано из избранного"
        event_name = "favorite_removed"
    else:
        can_add, limit = can_add_to_favorites(user)

        if not can_add:
            await callback.answer(
                f"Лимит избранного: {limit}. Премиум откроет безлимит.",
                show_alert=True,
            )
            return

        add_to_favorites(user_id, content_type, content_id)
        is_fav = True
        action_text = "Добавлено в избранное"
        event_name = "favorite_added"

    track_event(
        user_id,
        event_name,
        content_type=content_type,
        content_id=content_id,
        source=current_source,
        metadata={"vibe": vibe, "collection_name": collection_name},
    )

    keyboard = build_current_card_keyboard(
        data=data,
        user=user,
        view="main",
        is_favorite=is_fav,
        user_rating=get_user_rating(user_id, content_type, content_id),
    )
    if not keyboard:
        await callback.answer("Неизвестный тип", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(action_text)
