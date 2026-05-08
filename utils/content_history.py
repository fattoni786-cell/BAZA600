from utils.db import get_recently_viewed_content, mark_content_viewed
from utils.analytics import track_event

CONTENT_HIDE_DAYS = 60


def get_recently_seen_titles(user_id: int, content_type: str) -> set[str]:
    return set(get_recently_viewed_content(user_id, content_type, CONTENT_HIDE_DAYS))


def record_content_impression(user_id: int, content_type: str, title: str):
    mark_content_viewed(user_id, content_type, title)
    track_event(
        user_id=user_id,
        event_name="content_shown",
        content_type=content_type,
        content_id=title,
    )
