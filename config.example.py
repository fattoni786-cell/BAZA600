import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
BAZA_DB_PATH = os.getenv("BAZA_DB_PATH", "runtime/baza_users.db")

PREMIUM_PLANS = {
    "premium_6_days": {
        "days": 6,
        "price_xtr": 66,
    },
    "premium_60_days": {
        "days": 60,
        "price_xtr": 199,
    },
    "premium_600_days": {
        "days": 600,
        "price_xtr": 600,
    },
}
