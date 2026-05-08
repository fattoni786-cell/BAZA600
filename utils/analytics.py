import json

from utils.db import execute, fetch_all, fetch_one


def track_event(
    user_id: int | None,
    event_name: str,
    content_type: str | None = None,
    content_id: str | None = None,
    source: str | None = None,
    metadata: dict | None = None,
):
    if not event_name:
        return

    try:
        execute("""
        INSERT INTO analytics_events (
            user_id, event_name, content_type, content_id, source, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            event_name,
            content_type,
            content_id,
            source,
            json.dumps(metadata or {}, ensure_ascii=False),
        ))
    except Exception:
        # Analytics must never break the user flow.
        return


def scalar(query: str, params=()) -> int:
    row = fetch_one(query, params)
    return int(row[0] or 0) if row else 0


def get_analytics_summary() -> dict:
    return {
        "users_total": scalar("SELECT COUNT(*) FROM users"),
        "users_24h": scalar("""
            SELECT COUNT(*) FROM users
            WHERE datetime(created_at) >= datetime('now', '-1 day')
        """),
        "users_7d": scalar("""
            SELECT COUNT(*) FROM users
            WHERE datetime(created_at) >= datetime('now', '-7 days')
        """),
        "premium_total": scalar("""
            SELECT COUNT(*) FROM users
            WHERE role = 'premium'
              AND (premium_until IS NULL OR datetime(premium_until) > datetime('now'))
        """),
        "events_24h": scalar("""
            SELECT COUNT(*) FROM analytics_events
            WHERE datetime(created_at) >= datetime('now', '-1 day')
        """),
        "events_7d": scalar("""
            SELECT COUNT(*) FROM analytics_events
            WHERE datetime(created_at) >= datetime('now', '-7 days')
        """),
        "active_users_24h": scalar("""
            SELECT COUNT(DISTINCT user_id) FROM analytics_events
            WHERE user_id IS NOT NULL
              AND datetime(created_at) >= datetime('now', '-1 day')
        """),
        "active_users_7d": scalar("""
            SELECT COUNT(DISTINCT user_id) FROM analytics_events
            WHERE user_id IS NOT NULL
              AND datetime(created_at) >= datetime('now', '-7 days')
        """),
    }


def get_event_counts(days: int = 7, limit: int = 12):
    return fetch_all("""
    SELECT event_name, COUNT(*) AS count
    FROM analytics_events
    WHERE datetime(created_at) >= datetime('now', ?)
    GROUP BY event_name
    ORDER BY count DESC, event_name ASC
    LIMIT ?
    """, (f"-{days} days", limit))


def get_content_shown_by_type(days: int = 7):
    return fetch_all("""
    SELECT content_type, COUNT(*) AS count
    FROM analytics_events
    WHERE event_name = 'content_shown'
      AND content_type IS NOT NULL
      AND datetime(created_at) >= datetime('now', ?)
    GROUP BY content_type
    ORDER BY count DESC, content_type ASC
    """, (f"-{days} days",))


def get_top_content(days: int = 7, limit: int = 10):
    return fetch_all("""
    SELECT content_type, content_id, COUNT(*) AS count
    FROM analytics_events
    WHERE event_name = 'content_shown'
      AND content_id IS NOT NULL
      AND datetime(created_at) >= datetime('now', ?)
    GROUP BY content_type, content_id
    ORDER BY count DESC, content_id ASC
    LIMIT ?
    """, (f"-{days} days", limit))


def get_top_sources(days: int = 7, limit: int = 10):
    return fetch_all("""
    SELECT source, COUNT(*) AS count
    FROM analytics_events
    WHERE source IS NOT NULL
      AND datetime(created_at) >= datetime('now', ?)
    GROUP BY source
    ORDER BY count DESC, source ASC
    LIMIT ?
    """, (f"-{days} days", limit))
