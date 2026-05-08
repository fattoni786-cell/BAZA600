from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from utils.users import get_or_create_user, normalize_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:

        if hasattr(event, "from_user") and event.from_user:
            user = get_or_create_user(event.from_user.id)
            user = normalize_user(user)

            # прокидываем user во ВСЕ хендлеры
            data["user"] = user

        return await handler(event, data)
