from datetime import datetime, timedelta

from utils.db import execute, fetch_one


def get_or_create_user(telegram_id: int):
    user = fetch_one(
        "SELECT telegram_id, role, premium_until FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )

    if not user:
        execute(
            "INSERT INTO users (telegram_id) VALUES (?)",
            (telegram_id,),
        )
        user = fetch_one(
            "SELECT telegram_id, role, premium_until FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )

    return {
        "telegram_id": user[0],
        "role": user[1],
        "premium_until": user[2],
    }


def is_premium(user: dict) -> bool:
    if user["role"] != "premium":
        return False

    if user["premium_until"] is None:
        return True

    return datetime.utcnow() < datetime.fromisoformat(user["premium_until"])


def normalize_user(user: dict):
    if user["role"] == "premium" and user["premium_until"]:
        if datetime.utcnow() >= datetime.fromisoformat(user["premium_until"]):
            execute(
                "UPDATE users SET role = 'free', premium_until = NULL WHERE telegram_id = ?",
                (user["telegram_id"],),
            )
            user["role"] = "free"
            user["premium_until"] = None

    return user


def activate_premium(telegram_id: int, duration_days: int) -> str:
    user = get_or_create_user(telegram_id)
    now = datetime.utcnow()

    if user["premium_until"]:
        try:
            premium_until = datetime.fromisoformat(user["premium_until"])
        except ValueError:
            premium_until = now
    else:
        premium_until = now

    start_from = premium_until if premium_until > now else now
    new_premium_until = start_from + timedelta(days=duration_days)
    premium_until_value = new_premium_until.isoformat()

    execute(
        "UPDATE users SET role = 'premium', premium_until = ? WHERE telegram_id = ?",
        (premium_until_value, telegram_id),
    )

    return premium_until_value


def record_premium_payment(
    telegram_id: int,
    payload: str,
    amount: int,
    currency: str,
    telegram_payment_charge_id: str,
    provider_payment_charge_id: str | None,
    premium_until: str,
):
    execute(
        """
        INSERT OR IGNORE INTO premium_payments (
            telegram_id,
            payload,
            amount,
            currency,
            telegram_payment_charge_id,
            provider_payment_charge_id,
            premium_until
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            payload,
            amount,
            currency,
            telegram_payment_charge_id,
            provider_payment_charge_id,
            premium_until,
        ),
    )
