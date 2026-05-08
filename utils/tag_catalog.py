from utils.personal_anime import TAG_EXPLANATIONS as ANIME_PERSONAL_TAGS
from utils.personal_books import TAG_EXPLANATIONS as BOOK_PERSONAL_TAGS
from utils.personal_games import TAG_EXPLANATIONS as GAME_PERSONAL_TAGS
from utils.personal_movies import TAG_EXPLANATIONS as MOVIE_PERSONAL_TAGS
from utils.personal_series import TAG_EXPLANATIONS as SERIES_PERSONAL_TAGS
from utils.public_vibes import get_public_vibes


def humanize_tag(tag: str) -> str:
    return tag.replace("_", " ").title()


EXTRA_TAG_LABELS_BY_TYPE = {
    "book": {
        "atmospheric": "🌫 Атмосферно и тягуче",
        "chill": "😌 Спокойно выдохнуть",
        "dark_drama": "🌑 Тяжёлая тёмная драма",
    },
}


def build_tag_catalog(
    primary: dict[str, str],
    extra_tags: set[str],
    extra_labels: dict[str, str] | None = None,
) -> dict[str, str]:
    catalog = dict(primary)
    extra_labels = extra_labels or {}

    for tag in sorted(extra_tags):
        catalog.setdefault(tag, extra_labels.get(tag, f"➕ {humanize_tag(tag)}"))

    return catalog


EXTRA_TAGS_BY_TYPE = {
    "anime": set(ANIME_PERSONAL_TAGS.keys()),
    "movie": set(MOVIE_PERSONAL_TAGS.keys()),
    "game": set(GAME_PERSONAL_TAGS.keys()),
    "book": set(BOOK_PERSONAL_TAGS.keys()),
    "series": set(SERIES_PERSONAL_TAGS.keys()),
}


def get_tag_catalog(content_type: str) -> dict[str, str]:
    return build_tag_catalog(
        get_public_vibes(content_type),
        EXTRA_TAGS_BY_TYPE.get(content_type, set()),
        EXTRA_TAG_LABELS_BY_TYPE.get(content_type),
    )


TAG_CATALOG_BY_TYPE = {
    content_type: get_tag_catalog(content_type)
    for content_type in EXTRA_TAGS_BY_TYPE
}
