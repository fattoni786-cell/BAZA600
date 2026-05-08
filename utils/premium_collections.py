import random

from data.add_movies import load_movies
from data.anime import load_anime
from data.books import load_books
from data.games import load_games
from data.series import load_series
from utils.content_history import get_recently_seen_titles

LOADERS_BY_TYPE = {
    "anime": load_anime,
    "movie": load_movies,
    "game": load_games,
    "book": load_books,
    "series": load_series,
}


def get_collection_items(
    content_type: str,
    collection_name: str,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[dict]:
    loader = LOADERS_BY_TYPE[content_type]
    if content_type == "game":
        items = loader(platform=platform)
    else:
        items = loader()

    return [
        item
        for item in items
        if collection_name in item.get("premium_collections", [])
    ]


def normalize_collection_names(raw_text: str) -> list[str]:
    chunks = raw_text.replace("\n", ";").replace(",", ";").split(";")
    result = []

    for chunk in chunks:
        name = chunk.strip()
        if name and name not in result:
            result.append(name)

    return result


def get_all_collection_names(
    content_type: str,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[str]:
    loader = LOADERS_BY_TYPE[content_type]
    if content_type == "game":
        items = loader(platform=platform)
    else:
        items = loader()

    seen = []

    for item in items:
        for name in item.get("premium_collections", []):
            if name and name not in seen:
                seen.append(name)

    return seen


def get_random_collection_names(
    content_type: str,
    count: int = 3,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> list[str]:
    names = get_all_collection_names(content_type, platform=platform)
    if not names:
        return []

    if len(names) <= count:
        return names

    return random.sample(names, k=count)


def get_random_item_from_collection(
    content_type: str,
    collection_name: str,
    user_id: int,
    extra_excluded_titles: set[str] | None = None,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
):
    excluded_titles = set(get_recently_seen_titles(user_id, content_type))
    if extra_excluded_titles:
        excluded_titles.update(extra_excluded_titles)

    matching = get_collection_items(content_type, collection_name, platform=platform)
    if not matching:
        return None

    available = [item for item in matching if item["title"] not in excluded_titles]
    if not available:
        return None

    return random.choice(available)


def has_more_in_collection(
    content_type: str,
    collection_name: str,
    user_id: int,
    current_title: str | None = None,
    platform: str | list[str] | tuple[str, ...] | set[str] | None = None,
) -> bool:
    extra_excluded_titles = {current_title} if current_title else set()
    return bool(
        get_random_item_from_collection(
            content_type=content_type,
            collection_name=collection_name,
            user_id=user_id,
            extra_excluded_titles=extra_excluded_titles,
            platform=platform,
        )
    )
