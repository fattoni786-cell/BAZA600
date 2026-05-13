from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.games import (
    GAME_PLATFORMS,
    get_game_platform_label,
    get_game_platforms_icons_text,
    get_game_platforms_text,
    normalize_game_platforms,
    normalize_platform_filter,
    get_random_game,
    load_games,
)
from keyboards.common.premium_collections import premium_collections_keyboard
from keyboards.games.menu import games_mode_kb
from keyboards.games.personal import (
    game_personal_question_keyboard,
    game_personal_prompt_keyboard,
    personal_game_keyboard,
)
from keyboards.games.platforms import game_platform_keyboard
from keyboards.games.vibes import another_game_keyboard, game_vibe_keyboard
from states.game_personal import GamePersonalQuiz
from utils.access import (
    consume_free_personal_use,
    consume_premium_personal_use,
    free_personal_locked_text,
    free_personal_status,
    has_premium_access,
    premium_feature_locked_text,
    premium_personal_locked_text,
    premium_personal_status,
)
from utils.ai_fallback import ai_unavailable_text
from utils.ai_clarification import combine_prompt_with_clarification, personal_clarification_question
from utils.ai_rate_limit import ai_rate_limit_text, check_ai_request_limit
from utils.ai_personal_content import recommend_content_from_prompt
from utils.content_history import get_recently_seen_titles, record_content_impression
from utils.db import (
    get_user_game_platforms,
    get_user_rating,
    is_in_favorites,
    set_user_game_platforms,
)
from utils.fast_vibes import has_more_in_fast_vibe
from utils.flow_fx import pick_phrase, pulse_chat_action, show_transition_screen
from utils.llm_client import LLMClientError, LLMNotConfiguredError
from utils.media_sender import send_media
from utils.personal_games import (
    QUESTION_COUNT,
    get_question,
    pick_random_questions,
    recommend_games,
)
from utils.premium_collections import (
    get_random_collection_names,
    get_random_item_from_collection,
    has_more_in_collection,
)
from utils.text_limits import (
    MAX_AI_PROMPT_LENGTH,
    MIN_AI_PROMPT_LENGTH,
    clean_user_text,
    is_too_long,
    length_error_text,
)
from utils.ui import delete_tracked_message, replace_screen, replace_with_new_screen, track_active_screen

router = Router()

GAME_TRANSITION_LINES = [
    "Смотрю, во что тебе сейчас реально захочется провалиться.",
    "Проверяю, где у тебя сейчас лучший игровой ритм.",
    "Ловлю игру, которая не отпустит слишком быстро.",
    "Собираю не жанр, а твой текущий импульс.",
]


def current_game_platforms(data: dict) -> list[str]:
    return normalize_platform_filter(data.get("current_game_platforms")) or []


def build_game_context_note(
    platforms: list[str],
    collection_name: str | None = None,
    item: dict | None = None,
) -> str:
    parts = []
    item_platforms = normalize_game_platforms(item.get("platforms")) if item else platforms

    if item_platforms:
        platforms_text = ", ".join(
            get_game_platform_label(platform)
            for platform in item_platforms
        )
        parts.append(f"Платформы: <b>{platforms_text}</b>")

    if collection_name:
        parts.append(f"💎 Подборка: <b>{collection_name}</b>")

    return "\n".join(parts)


def get_game_by_title(title: str) -> dict | None:
    for game in load_games():
        if game["title"] == title:
            return game
    return None


async def sync_game_platforms(state: FSMContext, user_id: int) -> list[str]:
    data = await state.get_data()
    state_platforms = current_game_platforms(data)
    if state_platforms:
        return state_platforms

    saved_platforms = normalize_platform_filter(get_user_game_platforms(user_id)) or []
    if saved_platforms:
        await state.update_data(current_game_platforms=saved_platforms)
    return saved_platforms


async def show_game_platform_screen(callback: CallbackQuery, state: FSMContext, user_id: int):
    selected = await sync_game_platforms(state, user_id)
    selected_count = len(selected)

    extra = (
        f"\n\nСейчас выбрано: <b>{selected_count}</b>"
        if selected_count
        else ""
    )

    await replace_screen(
        callback,
        text=(
            "🎮 <b>Игры</b>\n\n"
            "Выбери платформы, на которых играешь."
            f"{extra}"
        ),
        reply_markup=game_platform_keyboard(selected),
    )


async def show_game_mode_screen(callback: CallbackQuery, platforms: list[str]):
    await replace_screen(
        callback,
        text=(
            "🎮 <b>Игры</b>\n\n"
            f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
            "Как будем подбирать игру?"
        ),
        reply_markup=games_mode_kb(),
    )


async def show_game_collections_screen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get("game_collection_options", [])
    platforms = current_game_platforms(data)

    await replace_screen(
        callback,
        text=(
            "💎 <b>Premium-подборки игр</b>\n\n"
            f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
            "Здесь собраны уже готовые тематические сценарии, а не просто вайбы."
        ),
        reply_markup=premium_collections_keyboard(
            options=options,
            pick_prefix="game_collection_pick",
            refresh_callback="games_collections_refresh",
        ),
    )


async def show_game_personal_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("game_personal_question_ids", [])
    current_index = data.get("game_personal_question_index", 0)
    platforms = current_game_platforms(data)

    if current_index >= len(question_ids):
        await callback.answer("Вопросы закончились")
        return

    question = get_question(question_ids[current_index])
    total = len(question_ids)
    text = (
        "🧠 <b>Персональный подбор игры</b>\n\n"
        f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
        "Отвечай быстро и без долгих раздумий. Я попробую выцепить твой сегодняшний игровой ритм.\n\n"
        f"<b>{question['text']}</b>"
    )

    await replace_screen(
        callback,
        text=text,
        reply_markup=game_personal_question_keyboard(
            answers=[answer["text"] for answer in question["answers"]],
            current_index=current_index,
            total=total,
        ),
    )


async def show_personal_game_result(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
    candidate_index: int,
):
    data = await state.get_data()
    candidates = data.get("game_personal_candidates", [])
    platforms = current_game_platforms(data)

    if candidate_index < 0 or candidate_index >= len(candidates):
        await callback.answer("Запасных вариантов больше нет", show_alert=True)
        return

    candidate = candidates[candidate_index]
    game = get_game_by_title(candidate["title"])

    if not game:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])
    has_backup = candidate_index < len(candidates) - 1

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=None,
        current_source="game_personal",
        current_caption_extra=candidate["explanation"],
        personal_candidate_index=candidate_index,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=personal_game_keyboard(
            has_backup=has_backup,
            title=game["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=candidate["explanation"],
        context_note=build_game_context_note(platforms, item=game),
    )


@router.callback_query(F.data == "choose_game")
async def choose_game(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.clear()
    platforms = normalize_platform_filter(get_user_game_platforms(user["telegram_id"])) or []
    if platforms:
        await state.update_data(current_game_platforms=platforms)
        await show_game_mode_screen(callback, platforms)
        return

    await show_game_platform_screen(callback, state, user["telegram_id"])


@router.callback_query(F.data == "games_platforms")
async def games_platforms(callback: CallbackQuery, user: dict, state: FSMContext):
    await show_game_platform_screen(callback, state, user["telegram_id"])


@router.callback_query(F.data.startswith("toggle_game_platform:"))
async def toggle_game_platform(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    selected = current_game_platforms(data)
    if not selected:
        selected = normalize_platform_filter(get_user_game_platforms(user["telegram_id"])) or []

    platform = callback.data.split(":", 1)[1]
    if platform not in GAME_PLATFORMS:
        await callback.answer("Платформа не найдена", show_alert=True)
        return

    if platform in selected:
        selected.remove(platform)
        await callback.answer("Платформа снята")
    else:
        selected.append(platform)
        await callback.answer("Платформа добавлена")

    await state.update_data(current_game_platforms=selected)
    await show_game_platform_screen(callback, state, user["telegram_id"])


@router.callback_query(F.data == "save_game_platforms")
async def save_game_platforms(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await callback.answer("Выбери хотя бы одну платформу", show_alert=True)
        return

    set_user_game_platforms(user["telegram_id"], platforms)
    await state.update_data(current_game_platforms=platforms)
    await callback.answer("Платформы сохранены")
    await show_game_mode_screen(callback, platforms)


@router.callback_query(F.data == "games_fast")
async def games_fast(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.update_data(fast_vibe_seen_count=0)
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    excluded_titles = get_recently_seen_titles(user["telegram_id"], "game")
    keyboard = game_vibe_keyboard(excluded_titles=excluded_titles, platform=platforms)
    text = f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\nКакой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
            "По играм ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    sent_message = await replace_with_new_screen(callback, text=text, reply_markup=keyboard)
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "games_surprise")
async def games_surprise(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    game = get_random_game(
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "game"),
        platform=platforms,
    )

    if not game:
        await callback.answer("На этих платформах пока нечего показать", show_alert=True)
        return

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=None,
        current_source="game_surprise",
        current_caption_extra=None,
        current_game_platforms=platforms,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=another_game_keyboard(
            vibe=None,
            title=game["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=build_game_context_note(platforms, item=game),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "games_personal")
async def games_personal(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    if has_premium_access(user):
        can_use, next_available_at, _remaining = premium_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=premium_personal_locked_text("Персональный подбор игр", next_available_at),
                reply_markup=games_mode_kb(),
            )
            return
        consume_premium_personal_use(user["telegram_id"])
    else:
        can_use, next_available_at = free_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=free_personal_locked_text("Персональный подбор игр", next_available_at),
                reply_markup=games_mode_kb(),
            )
            return
        consume_free_personal_use(user["telegram_id"])

    await state.set_state(GamePersonalQuiz.describing)
    await state.update_data(
        game_personal_candidates=[],
        personal_candidate_index=0,
        current_game_platforms=platforms,
        current_source=None,
        current_caption_extra=None,
        pending_ai_prompt=None,
    )

    await delete_tracked_message(state, callback.bot, callback.message.chat.id, "last_personal_prompt_message_id")
    prompt_message = await replace_with_new_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор игры</b>\n\n"
            f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
            "Опиши, во что хочется провалиться: темп, настроение, сложность, "
            "соло или кооп, сколько есть времени и чего точно не надо.\n\n"
            "Например:\n"
            "<i>Хочу одиночную игру на вечер, мрачную, но не душную. "
            "Чтобы было исследование и чувство опасности.</i>"
        ),
        reply_markup=game_personal_prompt_keyboard(),
    )
    if prompt_message:
        await state.update_data(last_personal_prompt_message_id=prompt_message.message_id)


@router.message(GamePersonalQuiz.describing, F.text)
async def game_personal_description(message: Message, user: dict, state: FSMContext):
    user_prompt = clean_user_text(message.text)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    state_data = await state.get_data()
    pending_ai_prompt = clean_user_text(state_data.get("pending_ai_prompt") or "")
    has_pending_ai_prompt = bool(pending_ai_prompt)
    if has_pending_ai_prompt:
        user_prompt = combine_prompt_with_clarification(pending_ai_prompt, user_prompt)
        await state.update_data(pending_ai_prompt=None)

    platforms = current_game_platforms(state_data)

    if not platforms:
        platforms = normalize_platform_filter(get_user_game_platforms(user["telegram_id"])) or []
        if platforms:
            await state.update_data(current_game_platforms=platforms)

    if not platforms:
        await message.answer("Сначала выбери платформы в разделе игр.")
        return

    if len(user_prompt) < MIN_AI_PROMPT_LENGTH:
        await message.answer("Опиши чуть подробнее: темп, настроение и чего избегаем.")
        return
    if is_too_long(user_prompt, MAX_AI_PROMPT_LENGTH):
        await message.answer(length_error_text(MAX_AI_PROMPT_LENGTH))
        return

    if not has_pending_ai_prompt:
        clarification_question = personal_clarification_question("game", user_prompt)
        if clarification_question:
            clarification_message = await message.answer(clarification_question)
            await state.update_data(
                pending_ai_prompt=user_prompt,
                last_personal_prompt_message_id=clarification_message.message_id,
            )
            return

    can_request_ai, retry_after = check_ai_request_limit(user["telegram_id"])
    if not can_request_ai:
        await message.answer(ai_rate_limit_text(retry_after))
        return

    processing_message = await message.answer("🧠 Сверяю твой вайб с базой игр...")
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.UPLOAD_PHOTO,
    )

    try:
        recommendations = await recommend_content_from_prompt(
            content_type="game",
            user_id=user["telegram_id"],
            user_prompt=user_prompt,
            platform=platforms,
        )
    except (LLMNotConfiguredError, LLMClientError):
        await state.clear()
        await state.update_data(current_game_platforms=platforms)
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=games_mode_kb(),
        )
        return

    if not recommendations:
        await state.clear()
        await state.update_data(current_game_platforms=platforms)
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=games_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        game_personal_candidates=[
            {
                "title": result["item"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
        current_game_platforms=platforms,
    )

    game = recommendations[0]["item"]
    explanation = recommendations[0]["explanation"]
    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])
    has_backup = len(recommendations) > 1

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=None,
        current_source="game_personal",
        current_caption_extra=explanation,
        personal_candidate_index=0,
        current_game_platforms=platforms,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    try:
        await processing_message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=message,
        item=game,
        content_type="game",
        reply_markup=personal_game_keyboard(
            has_backup=has_backup,
            title=game["title"],
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=explanation,
        context_note=build_game_context_note(platforms, item=game),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "games_collections")
async def games_collections(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    if not has_premium_access(user):
        await replace_screen(
            callback,
            text=premium_feature_locked_text("Premium-подборки игр"),
            reply_markup=games_mode_kb(),
        )
        return

    options = get_random_collection_names("game", count=3, platform=platforms)
    if not options:
        await replace_screen(
            callback,
            text=(
                f"💎 Для {get_game_platforms_text(platforms)} premium-подборок игр пока нет. "
                "Добавь их через /add."
            ),
            reply_markup=games_mode_kb(),
        )
        return

    await state.update_data(game_collection_options=options, current_game_platforms=platforms)
    await show_game_collections_screen(callback, state)


@router.callback_query(F.data == "games_collections_refresh")
async def games_collections_refresh(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    if not has_premium_access(user):
        await callback.answer("Подборки доступны только в Premium", show_alert=True)
        return

    options = get_random_collection_names("game", count=3, platform=platforms)
    await state.update_data(game_collection_options=options, current_game_platforms=platforms)
    await show_game_collections_screen(callback, state)


@router.callback_query(F.data.startswith("game_collection_pick:"))
async def game_collection_pick(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    options = data.get("game_collection_options", [])
    platforms = current_game_platforms(data)
    index = int(callback.data.split(":", 1)[1])

    if index < 0 or index >= len(options):
        await callback.answer("Подборка не найдена", show_alert=True)
        return

    collection_name = options[index]
    game = get_random_item_from_collection(
        content_type="game",
        collection_name=collection_name,
        user_id=user["telegram_id"],
        platform=platforms,
    )

    if not game:
        await callback.answer("В этой подборке пока ничего нет", show_alert=True)
        return

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=None,
        current_source="game_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
        current_game_platforms=platforms,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])
    show_next_collection = has_more_in_collection(
        "game",
        collection_name,
        user["telegram_id"],
        current_title=game["title"],
        platform=platforms,
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=another_game_keyboard(
            vibe=None,
            title=game["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=build_game_context_note(platforms, collection_name, item=game),
    )


@router.callback_query(F.data == "next_game_collection")
async def next_game_collection(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    collection_name = data.get("current_collection_name")
    platforms = current_game_platforms(data)

    if not collection_name:
        await callback.answer("Подборка уже закрыта", show_alert=True)
        return

    game = get_random_item_from_collection(
        content_type="game",
        collection_name=collection_name,
        user_id=user["telegram_id"],
        platform=platforms,
    )

    if not game:
        await callback.answer(
            "В этой подборке ты уже всё посмотрел за последнее время",
            show_alert=True,
        )
        return

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=None,
        current_source="game_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
        current_game_platforms=platforms,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])
    show_next_collection = has_more_in_collection(
        "game",
        collection_name,
        user["telegram_id"],
        current_title=game["title"],
        platform=platforms,
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=another_game_keyboard(
            vibe=None,
            title=game["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=build_game_context_note(platforms, collection_name, item=game),
    )


@router.callback_query(F.data == "game_personal_progress")
async def game_personal_progress(callback: CallbackQuery):
    await callback.answer("Просто выбирай вариант ниже")


@router.callback_query(GamePersonalQuiz.answering, F.data.startswith("game_personal_answer:"))
async def game_personal_answer(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("game_personal_question_ids", [])
    current_index = data.get("game_personal_question_index", 0)
    answers_history = data.get("game_personal_answers", [])

    if current_index >= len(question_ids):
        await callback.answer("Вопрос уже закрыт")
        return

    question = get_question(question_ids[current_index])
    answer_index = int(callback.data.split(":", 1)[1])

    if answer_index < 0 or answer_index >= len(question["answers"]):
        await callback.answer("Ответ не найден", show_alert=True)
        return

    answers_history.append(
        {
            "question_id": question["id"],
            "answer_index": answer_index,
        }
    )

    current_index += 1
    await state.update_data(
        game_personal_answers=answers_history,
        game_personal_question_index=current_index,
    )

    if current_index < len(question_ids):
        await pulse_chat_action(callback)
        await show_game_personal_question(callback, state)
        return

    recommendations = recommend_games(
        user_id=user["telegram_id"],
        answer_history=answers_history,
        platform=current_game_platforms(data),
    )

    if not recommendations:
        platforms = current_game_platforms(data)
        await state.clear()
        if platforms:
            await state.update_data(current_game_platforms=platforms)
        await replace_screen(
            callback,
            text=ai_unavailable_text(),
            reply_markup=games_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        game_personal_candidates=[
            {
                "title": result["game"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    await show_transition_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор игры</b>\n\n"
            f"{pick_phrase(GAME_TRANSITION_LINES)}"
        ),
        action="upload_photo",
    )
    await show_personal_game_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=0,
    )


@router.callback_query(F.data == "game_personal_backup")
async def game_personal_backup(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("personal_candidate_index", 0)

    await show_personal_game_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=current_index + 1,
    )


@router.callback_query(F.data.startswith("fast_game_vibe:"))
async def game_selected(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    platforms = current_game_platforms(data) or await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    vibe = callback.data.split(":", 1)[1]
    game = get_random_game(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "game"),
        platform=platforms,
    )

    if not game:
        await callback.answer("Игра не найдена", show_alert=True)
        return

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=vibe,
        current_source="game_fast",
        current_caption_extra=None,
        current_game_platforms=platforms,
        fast_vibe_seen_count=1,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    show_another = has_more_in_fast_vibe(
        "game",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "game"),
        platform=platforms,
    )
    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=another_game_keyboard(
            vibe=vibe,
            title=game["title"],
            show_another=show_another,
            show_change_vibe=False,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=build_game_context_note(platforms, item=game),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data.startswith("another_game:"))
async def another_game(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    platforms = current_game_platforms(data) or await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    vibe = callback.data.split(":", 1)[1]
    game = get_random_game(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "game"),
        platform=platforms,
    )

    if not game:
        await games_fast(callback, user, state)
        return

    seen_count = (
        int(data.get("fast_vibe_seen_count", 1)) + 1
        if data.get("current_vibe") == vibe and data.get("current_source") == "game_fast"
        else 1
    )

    await state.update_data(
        current_item=game,
        current_type="game",
        current_vibe=vibe,
        current_source="game_fast",
        current_caption_extra=None,
        current_game_platforms=platforms,
        fast_vibe_seen_count=seen_count,
    )
    record_content_impression(user["telegram_id"], "game", game["title"])

    show_another = has_more_in_fast_vibe(
        "game",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "game"),
        platform=platforms,
    )
    is_fav = is_in_favorites(user["telegram_id"], "game", game["title"])
    user_rating = get_user_rating(user["telegram_id"], "game", game["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=game,
        content_type="game",
        reply_markup=another_game_keyboard(
            vibe=vibe,
            title=game["title"],
            show_another=show_another,
            show_change_vibe=seen_count >= 2,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=build_game_context_note(platforms, item=game),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "refresh_game_vibes")
async def refresh_game_vibes(callback: CallbackQuery, user: dict, state: FSMContext):
    platforms = await sync_game_platforms(state, user["telegram_id"])
    if not platforms:
        await show_game_platform_screen(callback, state, user["telegram_id"])
        return

    excluded_titles = get_recently_seen_titles(user["telegram_id"], "game")
    keyboard = game_vibe_keyboard(excluded_titles=excluded_titles, platform=platforms)
    text = f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\nКакой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            f"🕹 <b>{get_game_platforms_icons_text(platforms)}</b>\n\n"
            "По играм ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    await replace_screen(callback, text=text, reply_markup=keyboard)

