from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from aiogram import Router, F
from aiogram.types import CallbackQuery


router = Router()   # ← ВОТ ЭТОГО У ТЕБЯ НЕ ХВАТАЛО


def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎬 Фильм",
                callback_data="choose_movie"
            )
        ]
    ])


@router.message(Command("start"))
async def start_handler(message: Message):
    # 🔥 СНАЧАЛА УБИРАЕМ СТАРЫЕ НИЖНИЕ КНОПКИ
    await message.answer(
        "Обновляем интерфейс 👌",
        reply_markup=ReplyKeyboardRemove()
    )

    # 🔥 ПОТОМ ПОКАЗЫВАЕМ INLINE-МЕНЮ
    await message.answer(
        "Что хочешь подобрать?",
        reply_markup=start_keyboard()
    )
@router.callback_query(F.data == "go_to_menu")
async def go_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Что хочешь подобрать?",
        reply_markup=start_keyboard()
    )

