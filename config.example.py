import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)) or default)
    except ValueError:
        return default


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
BAZA_DB_PATH = os.getenv("BAZA_DB_PATH", "runtime/baza_users.db")
PREMIUM_PROMO_CODES = {
    code.strip().upper()
    for code in os.getenv("PREMIUM_PROMO_CODES", "").split(",")
    if code.strip()
}
PREMIUM_PROMO_DAYS = _int_env("PREMIUM_PROMO_DAYS", 30)
PREMIUM_PROMO_MAX_REDEEMS = _int_env("PREMIUM_PROMO_MAX_REDEEMS", 0)

PREMIUM_PLANS = {
    "premium_6_days": {
        "days": 6,
        "price_xtr": 149,
    },
    "premium_60_days": {
        "days": 60,
        "price_xtr": 600,
    },
    "premium_600_days": {
        "days": 600,
        "price_xtr": 2999,
    },
}
