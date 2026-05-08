import asyncio
import random

from aiogram.enums import ChatAction
from aiogram.types import CallbackQuery

from utils.ui import replace_screen


async def pulse_chat_action(
    callback: CallbackQuery,
    action: ChatAction = ChatAction.TYPING,
    delay: float = 0.35,
):
    if callback.message is None:
        return

    await callback.answer()
    await callback.bot.send_chat_action(
        chat_id=callback.message.chat.id,
        action=action,
    )
    await asyncio.sleep(delay)


def pick_phrase(options: list[str]) -> str:
    return random.choice(options)


async def show_transition_screen(
    callback: CallbackQuery,
    text: str,
    action: ChatAction = ChatAction.TYPING,
    delay: float = 0.9,
):
    await replace_screen(callback, text=text)

    if callback.message is None:
        return

    await callback.bot.send_chat_action(
        chat_id=callback.message.chat.id,
        action=action,
    )
    await asyncio.sleep(delay)
