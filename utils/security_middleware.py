from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from config_baze.admins import ADMINS
from utils.db import is_user_blocked

BLOCKED_ALLOWED_COMMANDS = ("/privacy", "/delete_me")


class SecurityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if not from_user or from_user.id in ADMINS:
            return await handler(event, data)

        if is_user_blocked(from_user.id):
            if isinstance(event, Message) and (event.text or "").split(maxsplit=1)[0] in BLOCKED_ALLOWED_COMMANDS:
                return await handler(event, data)

            if isinstance(event, CallbackQuery):
                await event.answer("Доступ к боту ограничен.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("Доступ к боту ограничен.")
            return None

        return await handler(event, data)
