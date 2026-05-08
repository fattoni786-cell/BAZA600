from utils.db import (
    execute,
    init_admin_content_drafts,
    init_analytics_events,
    init_blocked_users,
    init_content_menu_preferences,
    init_content_suggestions,
    init_content_views,
    init_favorites,
    init_free_favorites_export_usage,
    init_free_personal_usage,
    init_game_platform_preferences,
    init_premium_reward_requests,
    init_ratings,
)


def init_users():
    execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            role TEXT NOT NULL DEFAULT 'free',
            premium_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


def init_premium_payments():
    execute("""
        CREATE TABLE IF NOT EXISTS premium_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            payload TEXT NOT NULL,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL,
            telegram_payment_charge_id TEXT NOT NULL UNIQUE,
            provider_payment_charge_id TEXT,
            premium_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)


def init_all():
    init_users()
    init_premium_payments()
    init_blocked_users()
    init_analytics_events()
    init_game_platform_preferences()
    init_content_menu_preferences()
    init_free_personal_usage()
    init_free_favorites_export_usage()
    init_favorites()
    init_ratings()
    init_content_views()
    init_content_suggestions()
    init_premium_reward_requests()
    init_admin_content_drafts()
