from data.add_movies import load_movies
from data.anime import load_anime
from data.books import load_books
from data.games import load_games
from data.series import load_series


LOADERS = {
    "movie": load_movies,
    "anime": load_anime,
    "book": load_books,
    "game": load_games,
    "series": load_series,
}


def has_more_in_fast_vibe(
    content_type: str,
    vibe: str | None,
    excluded_titles: set[str] | None = None,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> bool:
    if not vibe:
        return False

    loader = LOADERS.get(content_type)
    if not loader:
        return False

    excluded_titles = excluded_titles or set()
    if content_type == "game":
        items = loader(include_premium_collection_only=False, platform=platform)
    else:
        items = loader(include_premium_collection_only=False)

    return any(
        vibe in item.get("tags", []) and item["title"] not in excluded_titles
        for item in items
    )
