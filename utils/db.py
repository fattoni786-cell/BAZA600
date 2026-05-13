import json
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.getenv("BAZA_DB_PATH", "data/baza_users.db"))


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def execute(query, params=()):
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()


def fetch_one(query, params=()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()


def fetch_all(query, params=()):
    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


# =========================
# SECURITY / MODERATION
# =========================
def init_blocked_users():
    execute("""
    CREATE TABLE IF NOT EXISTS blocked_users (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        blocked_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def block_user(user_id: int, reason: str | None = None, blocked_by: int | None = None):
    execute("""
    INSERT INTO blocked_users (user_id, reason, blocked_by)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET
        reason = excluded.reason,
        blocked_by = excluded.blocked_by,
        created_at = CURRENT_TIMESTAMP
    """, (user_id, reason, blocked_by))


def unblock_user(user_id: int):
    execute("""
    DELETE FROM blocked_users
    WHERE user_id = ?
    """, (user_id,))


def is_user_blocked(user_id: int) -> bool:
    row = fetch_one("""
    SELECT 1
    FROM blocked_users
    WHERE user_id = ?
    """, (user_id,))
    return row is not None


def get_blocked_users(limit: int = 50):
    return fetch_all("""
    SELECT user_id, reason, blocked_by, created_at
    FROM blocked_users
    ORDER BY created_at DESC
    LIMIT ?
    """, (limit,))


def delete_user_data(user_id: int):
    execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
    execute("DELETE FROM ratings WHERE user_id = ?", (user_id,))
    execute("DELETE FROM content_views WHERE user_id = ?", (user_id,))
    execute("DELETE FROM analytics_events WHERE user_id = ?", (user_id,))
    execute("DELETE FROM game_platform_preferences WHERE user_id = ?", (user_id,))
    execute("DELETE FROM content_menu_preferences WHERE user_id = ?", (user_id,))
    execute("DELETE FROM free_personal_usage WHERE user_id = ?", (user_id,))
    execute("DELETE FROM premium_personal_usage WHERE user_id = ?", (user_id,))
    execute("DELETE FROM free_favorites_export_usage WHERE user_id = ?", (user_id,))
    execute("DELETE FROM blocked_users WHERE user_id = ?", (user_id,))
    execute("DELETE FROM content_suggestions WHERE user_id = ?", (user_id,))
    execute("DELETE FROM premium_reward_requests WHERE user_id = ?", (user_id,))
    execute("DELETE FROM admin_content_drafts WHERE suggested_by_user_id = ?", (user_id,))
    execute("DELETE FROM premium_payments WHERE telegram_id = ?", (user_id,))
    execute("DELETE FROM premium_promo_redemptions WHERE user_id = ?", (user_id,))
    execute("DELETE FROM users WHERE telegram_id = ?", (user_id,))


# =========================
# GAME PLATFORM PREFERENCES
# =========================
def init_game_platform_preferences():
    execute("""
    CREATE TABLE IF NOT EXISTS game_platform_preferences (
        user_id INTEGER PRIMARY KEY,
        platforms_json TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def get_user_game_platforms(user_id: int) -> list[str]:
    row = fetch_one("""
    SELECT platforms_json
    FROM game_platform_preferences
    WHERE user_id = ?
    """, (user_id,))

    if not row or not row[0]:
        return []

    try:
        value = json.loads(row[0])
    except json.JSONDecodeError:
        return []

    if not isinstance(value, list):
        return []

    result: list[str] = []
    for platform in value:
        if isinstance(platform, str) and platform not in result:
            result.append(platform)
    return result


def set_user_game_platforms(user_id: int, platforms: list[str]):
    execute("""
    INSERT INTO game_platform_preferences (user_id, platforms_json, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id)
    DO UPDATE SET
        platforms_json = excluded.platforms_json,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, json.dumps(platforms, ensure_ascii=False)))


# =========================
# CONTENT MENU PREFERENCES
# =========================
def init_content_menu_preferences():
    execute("""
    CREATE TABLE IF NOT EXISTS content_menu_preferences (
        user_id INTEGER PRIMARY KEY,
        content_types_json TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def get_user_content_menu_types(user_id: int) -> list[str]:
    row = fetch_one("""
    SELECT content_types_json
    FROM content_menu_preferences
    WHERE user_id = ?
    """, (user_id,))

    if not row or not row[0]:
        return []

    try:
        value = json.loads(row[0])
    except json.JSONDecodeError:
        return []

    if not isinstance(value, list):
        return []

    result: list[str] = []
    for content_type in value:
        if isinstance(content_type, str) and content_type not in result:
            result.append(content_type)
    return result


def set_user_content_menu_types(user_id: int, content_types: list[str]):
    execute("""
    INSERT INTO content_menu_preferences (user_id, content_types_json, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id)
    DO UPDATE SET
        content_types_json = excluded.content_types_json,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, json.dumps(content_types, ensure_ascii=False)))


# =========================
# ANALYTICS
# =========================
def init_analytics_events():
    execute("""
    CREATE TABLE IF NOT EXISTS analytics_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        event_name TEXT NOT NULL,
        content_type TEXT,
        content_id TEXT,
        source TEXT,
        metadata_json TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    execute("""
    CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at
    ON analytics_events(created_at)
    """)
    execute("""
    CREATE INDEX IF NOT EXISTS idx_analytics_events_user_created
    ON analytics_events(user_id, created_at)
    """)
    execute("""
    CREATE INDEX IF NOT EXISTS idx_analytics_events_name_created
    ON analytics_events(event_name, created_at)
    """)


# =========================
# FREE PERSONAL DAILY USAGE
# =========================
def init_free_personal_usage():
    execute("""
    CREATE TABLE IF NOT EXISTS free_personal_usage (
        user_id INTEGER PRIMARY KEY,
        last_used_at TEXT NOT NULL
    )
    """)


def get_free_personal_last_used(user_id: int) -> str | None:
    row = fetch_one("""
    SELECT last_used_at
    FROM free_personal_usage
    WHERE user_id = ?
    """, (user_id,))
    return row[0] if row else None


def set_free_personal_last_used(user_id: int, used_at: str):
    execute("""
    INSERT INTO free_personal_usage (user_id, last_used_at)
    VALUES (?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET last_used_at = excluded.last_used_at
    """, (user_id, used_at))


# =========================
# PREMIUM PERSONAL DAILY USAGE
# =========================
def init_premium_personal_usage():
    execute("""
    CREATE TABLE IF NOT EXISTS premium_personal_usage (
        user_id INTEGER NOT NULL,
        usage_date TEXT NOT NULL,
        used_count INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, usage_date)
    )
    """)


def get_premium_personal_used_count(user_id: int, usage_date: str) -> int:
    row = fetch_one("""
    SELECT used_count
    FROM premium_personal_usage
    WHERE user_id = ? AND usage_date = ?
    """, (user_id, usage_date))
    return row[0] if row else 0


def increment_premium_personal_used_count(user_id: int, usage_date: str):
    execute("""
    INSERT INTO premium_personal_usage (user_id, usage_date, used_count, updated_at)
    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id, usage_date)
    DO UPDATE SET
        used_count = used_count + 1,
        updated_at = CURRENT_TIMESTAMP
    """, (user_id, usage_date))


# =========================
# PREMIUM PROMO CODES
# =========================
def init_premium_promo_redemptions():
    execute("""
    CREATE TABLE IF NOT EXISTS premium_promo_redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        premium_until TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, code)
    )
    """)
    execute("""
    CREATE INDEX IF NOT EXISTS idx_premium_promo_redemptions_code
    ON premium_promo_redemptions(code)
    """)


def has_redeemed_promo_code(user_id: int, code: str) -> bool:
    row = fetch_one("""
    SELECT 1
    FROM premium_promo_redemptions
    WHERE user_id = ? AND code = ?
    """, (user_id, code))
    return row is not None


def count_promo_code_redemptions(code: str) -> int:
    row = fetch_one("""
    SELECT COUNT(*)
    FROM premium_promo_redemptions
    WHERE code = ?
    """, (code,))
    return row[0] if row else 0


def record_promo_code_redemption(user_id: int, code: str, premium_until: str):
    execute("""
    INSERT OR IGNORE INTO premium_promo_redemptions (
        user_id, code, premium_until
    )
    VALUES (?, ?, ?)
    """, (user_id, code, premium_until))


# =========================
# FREE FAVORITES EXPORT WEEKLY USAGE
# =========================
def init_free_favorites_export_usage():
    execute("""
    CREATE TABLE IF NOT EXISTS free_favorites_export_usage (
        user_id INTEGER PRIMARY KEY,
        last_used_at TEXT NOT NULL
    )
    """)


def get_free_favorites_export_last_used(user_id: int) -> str | None:
    row = fetch_one("""
    SELECT last_used_at
    FROM free_favorites_export_usage
    WHERE user_id = ?
    """, (user_id,))
    return row[0] if row else None


def set_free_favorites_export_last_used(user_id: int, used_at: str):
    execute("""
    INSERT INTO free_favorites_export_usage (user_id, last_used_at)
    VALUES (?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET last_used_at = excluded.last_used_at
    """, (user_id, used_at))


# =========================
# FAVORITES
# =========================
def init_favorites():
    execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        content_id TEXT NOT NULL,
        UNIQUE(user_id, content_type, content_id)
    )
    """)


def add_to_favorites(user_id: int, content_type: str, content_id: str):
    execute("""
    INSERT OR IGNORE INTO favorites (user_id, content_type, content_id)
    VALUES (?, ?, ?)
    """, (user_id, content_type, content_id))


def remove_from_favorites(user_id: int, content_type: str, content_id: str):
    execute("""
    DELETE FROM favorites
    WHERE user_id = ? AND content_type = ? AND content_id = ?
    """, (user_id, content_type, content_id))


def is_in_favorites(user_id: int, content_type: str, content_id: str) -> bool:
    row = fetch_one("""
    SELECT 1 FROM favorites
    WHERE user_id = ? AND content_type = ? AND content_id = ?
    """, (user_id, content_type, content_id))
    return row is not None


def get_user_favorites(user_id: int, content_type: str | None = None):
    if content_type:
        return fetch_all("""
        SELECT content_id FROM favorites
        WHERE user_id = ? AND content_type = ?
        """, (user_id, content_type))
    return fetch_all("""
    SELECT content_type, content_id FROM favorites
    WHERE user_id = ?
    """, (user_id,))


# =========================
# RATINGS
# =========================
def init_ratings():
    execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        content_id TEXT NOT NULL,
        value INTEGER NOT NULL,
        PRIMARY KEY (user_id, content_type, content_id)
    )
    """)


def set_rating(
    user_id: int,
    content_type: str,
    content_id: str,
    value: int
):
    execute("""
    INSERT INTO ratings (user_id, content_type, content_id, value)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, content_type, content_id)
    DO UPDATE SET value = excluded.value
    """, (user_id, content_type, content_id, value))


def remove_rating(
    user_id: int,
    content_type: str,
    content_id: str
):
    execute("""
    DELETE FROM ratings
    WHERE user_id = ? AND content_type = ? AND content_id = ?
    """, (user_id, content_type, content_id))


def get_user_rating(
    user_id: int,
    content_type: str,
    content_id: str
) -> int | None:
    row = fetch_one("""
    SELECT value FROM ratings
    WHERE user_id = ? AND content_type = ? AND content_id = ?
    """, (user_id, content_type, content_id))
    return row[0] if row else None


def get_user_rated_content(
    user_id: int,
    content_type: str,
    value: int | None = None
):
    if value is None:
        rows = fetch_all("""
        SELECT content_id FROM ratings
        WHERE user_id = ? AND content_type = ?
        """, (user_id, content_type))
    else:
        rows = fetch_all("""
        SELECT content_id FROM ratings
        WHERE user_id = ? AND content_type = ? AND value = ?
        """, (user_id, content_type, value))

    return [content_id for (content_id,) in rows]


def get_rating_summary(
    content_type: str,
    content_id: str
) -> dict:
    rows = fetch_all("""
    SELECT value, COUNT(*)
    FROM ratings
    WHERE content_type = ? AND content_id = ?
    GROUP BY value
    """, (content_type, content_id))

    likes = 0
    dislikes = 0
    mixed = 0
    base_approves = 0

    for value, count in rows:
        if value == 1:
            likes = count
        elif value == -1:
            dislikes = count
        elif value == 0:
            mixed = count
        elif value == 2:
            base_approves = count

    return {
        "likes": likes,
        "dislikes": dislikes,
        "mixed": mixed,
        "base_approves": base_approves,
        "score": likes - dislikes,
    }


def init_content_views():
    execute("""
    CREATE TABLE IF NOT EXISTS content_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        content_id TEXT NOT NULL,
        viewed_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def mark_content_viewed(user_id: int, content_type: str, content_id: str):
    execute("""
    INSERT INTO content_views (user_id, content_type, content_id)
    VALUES (?, ?, ?)
    """, (user_id, content_type, content_id))


def get_recently_viewed_content(
    user_id: int,
    content_type: str,
    days: int,
):
    rows = fetch_all("""
    SELECT DISTINCT content_id
    FROM content_views
    WHERE user_id = ?
      AND content_type = ?
      AND datetime(viewed_at) >= datetime('now', ?)
    """, (user_id, content_type, f"-{days} days"))
    return [content_id for (content_id,) in rows]


# =========================
# COMMUNITY CONTENT SUGGESTIONS
# =========================
def init_content_suggestions():
    execute("""
    CREATE TABLE IF NOT EXISTS content_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        vibe_text TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        admin_note TEXT,
        reviewed_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TEXT
    )
    """)


def create_content_suggestion(
    user_id: int,
    username: str | None,
    content_type: str,
    title: str,
    description: str,
    vibe_text: str,
):
    execute("""
    INSERT INTO content_suggestions (
        user_id, username, content_type, title, description, vibe_text
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, content_type, title, description, vibe_text))


def count_recent_content_suggestions(user_id: int, hours: int = 24) -> int:
    row = fetch_one("""
    SELECT COUNT(*)
    FROM content_suggestions
    WHERE user_id = ?
      AND datetime(created_at) >= datetime('now', ?)
    """, (user_id, f"-{hours} hours"))
    return row[0] if row else 0


def get_content_suggestion(suggestion_id: int):
    return fetch_one("""
    SELECT
        id, user_id, username, content_type, title, description, vibe_text,
        status, admin_note, reviewed_by, created_at, reviewed_at
    FROM content_suggestions
    WHERE id = ?
    """, (suggestion_id,))


def get_content_suggestions_by_status(status: str, limit: int = 20):
    return fetch_all("""
    SELECT
        id, user_id, username, content_type, title, description, vibe_text,
        status, created_at
    FROM content_suggestions
    WHERE status = ?
    ORDER BY created_at ASC, id ASC
    LIMIT ?
    """, (status, limit))


def update_content_suggestion_status(
    suggestion_id: int,
    status: str,
    reviewed_by: int,
    admin_note: str | None = None,
):
    execute("""
    UPDATE content_suggestions
    SET status = ?,
        reviewed_by = ?,
        admin_note = ?,
        reviewed_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (status, reviewed_by, admin_note, suggestion_id))


def get_user_suggestion_stats(user_id: int) -> dict[str, int]:
    rows = fetch_all("""
    SELECT status, COUNT(*)
    FROM content_suggestions
    WHERE user_id = ?
    GROUP BY status
    """, (user_id,))

    stats = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
    }

    for status, count in rows:
        if status in stats:
            stats[status] = count

    return stats


def get_contributor_overview(limit: int = 50):
    return fetch_all("""
    SELECT
        user_id,
        MAX(username) AS username,
        COUNT(*) AS total_sent,
        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_count,
        SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved_count,
        SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_count,
        MAX(created_at) AS last_submission_at
    FROM content_suggestions
    GROUP BY user_id
    ORDER BY approved_count DESC, total_sent DESC, pending_count DESC, user_id ASC
    LIMIT ?
    """, (limit,))


# =========================
# PREMIUM REWARD REQUESTS
# =========================
def init_premium_reward_requests():
    execute("""
    CREATE TABLE IF NOT EXISTS premium_reward_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        approved_count_snapshot INTEGER NOT NULL,
        slots_reserved INTEGER NOT NULL DEFAULT 6,
        status TEXT NOT NULL DEFAULT 'pending',
        reviewed_by INTEGER,
        premium_until TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        reviewed_at TEXT
    )
    """)


def create_premium_reward_request(user_id: int, approved_count_snapshot: int):
    execute("""
    INSERT INTO premium_reward_requests (
        user_id, approved_count_snapshot
    )
    VALUES (?, ?)
    """, (user_id, approved_count_snapshot))


def get_premium_reward_request(request_id: int):
    return fetch_one("""
    SELECT
        id, user_id, approved_count_snapshot, slots_reserved,
        status, reviewed_by, premium_until, created_at, reviewed_at
    FROM premium_reward_requests
    WHERE id = ?
    """, (request_id,))


def get_premium_reward_requests_by_status(status: str, limit: int = 20):
    return fetch_all("""
    SELECT
        id, user_id, approved_count_snapshot, slots_reserved,
        status, created_at
    FROM premium_reward_requests
    WHERE status = ?
    ORDER BY created_at ASC, id ASC
    LIMIT ?
    """, (status, limit))


def update_premium_reward_request_status(
    request_id: int,
    status: str,
    reviewed_by: int,
    premium_until: str | None = None,
):
    execute("""
    UPDATE premium_reward_requests
    SET status = ?,
        reviewed_by = ?,
        premium_until = ?,
        reviewed_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (status, reviewed_by, premium_until, request_id))


def get_reserved_reward_slots(user_id: int) -> int:
    row = fetch_one("""
    SELECT COALESCE(SUM(slots_reserved), 0)
    FROM premium_reward_requests
    WHERE user_id = ?
      AND status IN ('pending', 'approved')
    """, (user_id,))
    return row[0] if row else 0


def has_pending_premium_reward_request(user_id: int) -> bool:
    row = fetch_one("""
    SELECT 1
    FROM premium_reward_requests
    WHERE user_id = ?
      AND status = 'pending'
    LIMIT 1
    """, (user_id,))
    return row is not None


# =========================
# ADMIN CONTENT DRAFTS
# =========================
def init_admin_content_drafts():
    execute("""
    CREATE TABLE IF NOT EXISTS admin_content_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        suggestion_id INTEGER,
        suggested_by_user_id INTEGER,
        content_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        vibe_text TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        used_at TEXT
    )
    """)


def create_admin_content_draft(
    suggestion_id: int | None,
    suggested_by_user_id: int | None,
    content_type: str,
    title: str,
    description: str,
    vibe_text: str | None,
):
    execute("""
    INSERT INTO admin_content_drafts (
        suggestion_id, suggested_by_user_id, content_type,
        title, description, vibe_text
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        suggestion_id,
        suggested_by_user_id,
        content_type,
        title,
        description,
        vibe_text,
    ))

    row = fetch_one("SELECT last_insert_rowid()")
    return row[0] if row else None


def get_admin_content_drafts(status: str = "pending", limit: int = 20):
    return fetch_all("""
    SELECT
        id, suggestion_id, suggested_by_user_id, content_type,
        title, description, vibe_text, status, created_at
    FROM admin_content_drafts
    WHERE status = ?
    ORDER BY created_at ASC, id ASC
    LIMIT ?
    """, (status, limit))


def get_admin_content_draft(draft_id: int):
    return fetch_one("""
    SELECT
        id, suggestion_id, suggested_by_user_id, content_type,
        title, description, vibe_text, status, created_at, used_at
    FROM admin_content_drafts
    WHERE id = ?
    """, (draft_id,))


def mark_admin_content_draft_used(draft_id: int):
    execute("""
    UPDATE admin_content_drafts
    SET status = 'used',
        used_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (draft_id,))
