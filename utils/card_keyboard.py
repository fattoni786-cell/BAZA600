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
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_rating, is_in_favorites
from utils.fast_vibes import has_more_in_fast_vibe
from utils.premium_collections import has_more_in_collection


def build_current_card_keyboard(
    data: dict,
    user: dict,
    view: str = "main",
    is_favorite: bool | None = None,
    user_rating: int | None = None,
):
    item = data.get("current_item")
    content_type = data.get("current_type")
    vibe = data.get("current_vibe")
    current_source = data.get("current_source")
    collection_name = data.get("current_collection_name")

    if not item or not content_type:
        return None

    user_id = user["telegram_id"]
    title = item.get("title")
    is_premium = has_premium_access(user)
    is_favorite = (
        is_in_favorites(user_id, content_type, title)
        if is_favorite is None
        else is_favorite
    )
    user_rating = (
        get_user_rating(user_id, content_type, title)
        if user_rating is None
        else user_rating
    )
    game_platforms = data.get("current_game_platforms")
    fast_vibe_seen_count = data.get("fast_vibe_seen_count", 0)
    show_change_vibe = (
        bool(vibe)
        and isinstance(current_source, str)
        and current_source.endswith("_fast")
        and fast_vibe_seen_count >= 2
    )

    show_another = False
    if vibe:
        kwargs = {"platform": game_platforms} if content_type == "game" else {}
        show_another = has_more_in_fast_vibe(
            content_type,
            vibe,
            excluded_titles=get_recently_seen_titles(user_id, content_type),
            **kwargs,
        )

    show_next_collection = False
    if collection_name and current_source and current_source.endswith("_collection"):
        kwargs = {"platform": game_platforms} if content_type == "game" else {}
        show_next_collection = has_more_in_collection(
            content_type,
            collection_name,
            user_id,
            current_title=title,
            **kwargs,
        )

    if content_type == "anime":
        if current_source == "anime_personal":
            candidates = data.get("anime_personal_candidates", [])
            current_index = data.get("personal_candidate_index", 0)
            return personal_anime_keyboard(
                has_backup=current_index < len(candidates) - 1,
                title=title,
                is_favorite=is_favorite,
                user_rating=user_rating,
                is_premium=is_premium,
                view=view,
            )
        return another_anime_keyboard(
            vibe=vibe,
            title=title,
            show_another=show_another,
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            show_change_vibe=show_change_vibe,
            is_favorite=is_favorite,
            user_rating=user_rating,
            is_premium=is_premium,
            view=view,
        )

    if content_type == "book":
        has_audio = bool(item.get("audio") and item["audio"].get("file_id"))
        if current_source == "book_personal":
            candidates = data.get("book_personal_candidates", [])
            current_index = data.get("personal_candidate_index", 0)
            return personal_book_keyboard(
                has_backup=current_index < len(candidates) - 1,
                title=title,
                has_audio=has_audio,
                is_favorite=is_favorite,
                user_rating=user_rating,
                is_premium=is_premium,
                view=view,
            )
        return another_book_keyboard(
            vibe=vibe,
            title=title,
            show_another=show_another,
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            show_change_vibe=show_change_vibe,
            has_audio=has_audio,
            is_favorite=is_favorite,
            user_rating=user_rating,
            is_premium=is_premium,
            view=view,
        )

    if content_type == "movie":
        if current_source == "movie_personal":
            candidates = data.get("movie_personal_candidates", [])
            current_index = data.get("personal_candidate_index", 0)
            return personal_movie_keyboard(
                has_backup=current_index < len(candidates) - 1,
                title=title,
                is_favorite=is_favorite,
                user_rating=user_rating,
                is_premium=is_premium,
                view=view,
            )
        return another_movie_keyboard(
            vibe=vibe,
            title=title,
            show_another=show_another,
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            show_change_vibe=show_change_vibe,
            is_favorite=is_favorite,
            user_rating=user_rating,
            is_premium=is_premium,
            view=view,
        )

    if content_type == "game":
        if current_source == "game_personal":
            candidates = data.get("game_personal_candidates", [])
            current_index = data.get("personal_candidate_index", 0)
            return personal_game_keyboard(
                has_backup=current_index < len(candidates) - 1,
                title=title,
                is_favorite=is_favorite,
                user_rating=user_rating,
                is_premium=is_premium,
                view=view,
            )
        return another_game_keyboard(
            vibe=vibe,
            title=title,
            show_another=show_another,
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            show_change_vibe=show_change_vibe,
            is_favorite=is_favorite,
            user_rating=user_rating,
            is_premium=is_premium,
            view=view,
        )

    if content_type == "series":
        if current_source == "series_personal":
            candidates = data.get("series_personal_candidates", [])
            current_index = data.get("personal_candidate_index", 0)
            return personal_series_keyboard(
                has_backup=current_index < len(candidates) - 1,
                title=title,
                is_favorite=is_favorite,
                user_rating=user_rating,
                is_premium=is_premium,
                view=view,
            )
        return another_series_keyboard(
            vibe=vibe,
            title=title,
            show_another=show_another,
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            show_change_vibe=show_change_vibe,
            is_favorite=is_favorite,
            user_rating=user_rating,
            is_premium=is_premium,
            view=view,
        )

    return None
