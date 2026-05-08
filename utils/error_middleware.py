import logging
from pathlib import Path
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware

from utils.admin_notify import notify_admins


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "bot_errors.log",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class ErrorLoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as error:
            logging.exception("Unhandled bot error")

            bot = data.get("bot")
            from_user = getattr(event, "from_user", None)
            user_id = from_user.id if from_user else "unknown"
            if bot:
                await notify_admins(
                    bot,
                    f"⚠️ Ошибка в боте\nUser: {user_id}\n{type(error).__name__}: {error}",
                )

            return None
