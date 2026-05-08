import random

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from states.search import SearchFlow
from utils.access import has_premium_access
from utils.analytics import track_event
from utils.card_keyboard import build_current_card_keyboard
from utils.db import get_user_rating, is_in_favorites
from utils.media_sender import send_media
from utils.search import get_content_item, search_content, search_result_label
from utils.text_limits import clean_user_text
from utils.ui import replace_screen

router = Router()

MIN_SEARCH_QUERY_LENGTH = 2
MAX_SEARCH_QUERY_LENGTH = 80

EMPTY_SEARCH_PHRASES = [
    "Ничего не нашёл. База делает вид, что ей не стыдно.",
    "Увы, в базе такого пока нет. Но звучит подозрительно.",
    "Не нашёл. Возможно, это слишком элитно даже для нас.",
    "Пусто. База посмотрела в бездну, а бездна вышла из чата.",
    "Такого у нас пока нет. Но мы запомнили твоё культурное давление.",
    "Ноль совпадений. Контент ушёл в подполье.",
    "Не нашёл. Либо этого нет в базе, либо оно прячется.",
    "База молчит. Значит, либо редкость, либо опечатка, либо заговор.",
    "По этому запросу пусто. Попробуй не расстраиваться.",
    "Ничего не найдено. Алгоритм сделал вид, что занят.",
    "Такого пока нет. База пополняется, не напрягайся.",
    "Не нашли. Но твой запрос был принят с уважительным недоумением.",
    "Пусто. Возможно, ты ищешь слишком глубоко.",
    "Совпадений нет. Попробуй не отпускать надежду.",
    "База600 не знает такого. Неловко.",
    "Ничего. Даже Мистер600 не в курсе.",
    "Не найдено. Контентный след оборвался.",
    "У нас такого нет. Пока что. Интрига сохранена.",
    "Пусто. База официально делает вид, что это фича.",
    "Нет совпадений. Возможно, это название из параллельной вселенной.",
    "База порылась в карманах — там пусто.",
    "Не нашёл. Зато теперь у нас есть повод расширяться.",
    "Такого в архиве нет. Архив слегка покраснел.",
    "Пустой результат. Но мы оба знаем: ты не сдашься.",
    "Не найдено. Либо шедевр, либо ты опечатался.",
    "База не смогла. Да, такое тоже бывает.",
    "Совпадений нет. Культурная разведка провалена.",
    "Не нашли. Но звучит так, будто надо добавить.",
]


def search_prompt_text() -> str:
    return "<b>Напиши название</b>"


def search_results_keyboard(results) -> InlineKeyboardMarkup:
    buttons = []
    for result in results:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=search_result_label(result),
                    callback_data=f"search_open:{result.content_type}:{result.index}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="🔎 Искать ещё", callback_data="search_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("search"))
async def search_command(message: Message, state: FSMContext, user: dict):
    await state.set_state(SearchFlow.waiting_query)
    track_event(user["telegram_id"], "search_opened", source="command")
    await message.answer(search_prompt_text(), parse_mode="HTML")


@router.message(F.text == "🔎 Поиск")
async def search_bottom_button(message: Message, state: FSMContext, user: dict):
    await state.set_state(SearchFlow.waiting_query)
    track_event(user["telegram_id"], "search_opened", source="bottom_nav")
    await message.answer(search_prompt_text(), parse_mode="HTML")


@router.callback_query(F.data == "search_start")
async def search_start(callback: CallbackQuery, state: FSMContext, user: dict):
    await state.set_state(SearchFlow.waiting_query)
    track_event(user["telegram_id"], "search_opened", source="inline")
    await replace_screen(
        callback,
        text=search_prompt_text(),
    )


@router.message(SearchFlow.waiting_query, F.text)
async def search_receive_query(message: Message, state: FSMContext, user: dict):
    query = clean_user_text(message.text)

    if len(query) < MIN_SEARCH_QUERY_LENGTH:
        await message.answer("Напиши хотя бы 2 символа, чтобы было за что зацепиться.")
        return
    if len(query) > MAX_SEARCH_QUERY_LENGTH:
        await message.answer(f"Слишком длинный запрос. Давай до {MAX_SEARCH_QUERY_LENGTH} символов.")
        return

    results = search_content(
        query=query,
        is_premium=has_premium_access(user),
        limit=8,
    )
    await state.clear()

    track_event(
        user["telegram_id"],
        "search_used",
        source="global_search",
        metadata={"query": query, "results_count": len(results)},
    )

    if not results:
        await message.answer(
            random.choice(EMPTY_SEARCH_PHRASES),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔎 Искать ещё", callback_data="search_start")],
                ]
            ),
        )
        return

    await message.answer(
        "🔎 <b>Нашёл похожее</b>\n\nВыбери нужную карточку:",
        parse_mode="HTML",
        reply_markup=search_results_keyboard(results),
    )


@router.callback_query(F.data.startswith("search_open:"))
async def search_open(callback: CallbackQuery, state: FSMContext, user: dict):
    _, content_type, raw_index = callback.data.split(":", 2)

    if not raw_index.isdigit():
        await callback.answer("Карточка не найдена", show_alert=True)
        return

    item = get_content_item(content_type, int(raw_index))
    if not item:
        await callback.answer("Карточка не найдена", show_alert=True)
        return

    if item.get("premium_collection_only", False) and not has_premium_access(user):
        await callback.answer("Эта карточка лежит в Premium-подборках.", show_alert=True)
        return

    await state.update_data(
        current_item=item,
        current_type=content_type,
        current_vibe=None,
        current_source="search",
        current_caption_extra=None,
    )

    track_event(
        user["telegram_id"],
        "search_result_opened",
        content_type=content_type,
        content_id=item.get("title"),
        source="global_search",
    )

    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()
    is_fav = is_in_favorites(user["telegram_id"], content_type, item["title"])
    user_rating = get_user_rating(user["telegram_id"], content_type, item["title"])
    keyboard = build_current_card_keyboard(
        data,
        user,
        is_favorite=is_fav,
        user_rating=user_rating,
    )

    await send_media(
        callback=callback,
        item=item,
        content_type=content_type,
        reply_markup=keyboard,
    )
