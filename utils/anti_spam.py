from collections import defaultdict, deque
from time import monotonic
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from config_baze.admins import ADMINS


class AntiSpamMiddleware(BaseMiddleware):
    def __init__(
        self,
        message_limit: int = 6,
        message_window: float = 10.0,
        callback_limit: int = 12,
        callback_window: float = 10.0,
        duplicate_callback_cooldown: float = 0.7,
        warning_cooldown: float = 8.0,
    ):
        self.message_limit = message_limit
        self.message_window = message_window
        self.callback_limit = callback_limit
        self.callback_window = callback_window
        self.duplicate_callback_cooldown = duplicate_callback_cooldown
        self.warning_cooldown = warning_cooldown

        self._message_events = defaultdict(deque)
        self._callback_events = defaultdict(deque)
        self._last_callback_at = {}
        self._last_warning_at = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if not from_user or from_user.id in ADMINS:
            return await handler(event, data)

        if isinstance(event, Message) and event.successful_payment:
            return await handler(event, data)

        now = monotonic()
        if isinstance(event, CallbackQuery):
            if self._is_duplicate_callback(event, now):
                await event.answer("Уже обрабатываю, секунду.")
                return None

            if self._is_limited(
                self._callback_events[from_user.id],
                now,
                self.callback_window,
                self.callback_limit,
            ):
                await event.answer("Слишком быстро. Дай БАЗЕ пару секунд.", show_alert=True)
                return None

        elif isinstance(event, Message):
            if self._is_limited(
                self._message_events[from_user.id],
                now,
                self.message_window,
                self.message_limit,
            ):
                await self._warn_message(event, from_user.id, now)
                return None

        return await handler(event, data)

    def _is_limited(self, events: deque, now: float, window: float, limit: int) -> bool:
        while events and now - events[0] > window:
            events.popleft()

        events.append(now)
        return len(events) > limit

    def _is_duplicate_callback(self, event: CallbackQuery, now: float) -> bool:
        key = (event.from_user.id, event.data or "")
        last_at = self._last_callback_at.get(key)
        self._last_callback_at[key] = now
        return last_at is not None and now - last_at < self.duplicate_callback_cooldown

    async def _warn_message(self, message: Message, user_id: int, now: float):
        if now - self._last_warning_at[user_id] < self.warning_cooldown:
            return

        self._last_warning_at[user_id] = now
        await message.answer("Чуть тише, БАЗА переваривает вайб.")
