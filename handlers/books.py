from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data.books import get_random_book, load_books
from keyboards.books.menu import books_mode_kb
from keyboards.books.personal import (
    book_personal_prompt_keyboard,
    book_personal_question_keyboard,
    personal_book_keyboard,
)
from keyboards.books.vibes import another_book_keyboard, book_vibe_keyboard
from keyboards.common.premium_collections import premium_collections_keyboard
from states.book_personal import BookPersonalQuiz
from utils.access import (
    consume_free_personal_use,
    free_personal_locked_text,
    free_personal_status,
    has_premium_access,
    premium_feature_locked_text,
)
from utils.ai_fallback import ai_unavailable_text
from utils.ai_clarification import combine_prompt_with_clarification, personal_clarification_question
from utils.ai_rate_limit import ai_rate_limit_text, check_ai_request_limit
from utils.ai_personal_content import recommend_content_from_prompt
from utils.content_history import get_recently_seen_titles, record_content_impression
from utils.db import get_user_rating, is_in_favorites
from utils.flow_fx import pick_phrase, pulse_chat_action, show_transition_screen
from utils.fast_vibes import has_more_in_fast_vibe
from utils.llm_client import LLMClientError, LLMNotConfiguredError
from utils.media_sender import send_media
from utils.premium_collections import (
    get_random_collection_names,
    get_random_item_from_collection,
    has_more_in_collection,
)
from utils.personal_books import (
    QUESTION_COUNT,
    get_question,
    pick_random_questions,
    recommend_books,
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

BOOK_TRANSITION_LINES = [
    "Смотрю, какой текст сейчас ляжет в тебя тише и точнее.",
    "Пытаюсь найти книгу под твой внутренний ритм.",
    "Собираю не жанр, а нужное тебе состояние чтения.",
    "Проверяю, какая книга сейчас будет звучать особенно лично.",
]


def get_book_by_title(title: str) -> dict | None:
    for book in load_books():
        if book["title"] == title:
            return book
    return None


async def show_book_collections_screen(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    options = data.get("book_collection_options", [])

    await replace_screen(
        callback,
        text=(
            "💎 <b>Premium-подборки книг</b>\n\n"
            "Здесь уже не просто настроение, а готовые тематические заходы на чтение."
        ),
        reply_markup=premium_collections_keyboard(
            options=options,
            pick_prefix="book_collection_pick",
            refresh_callback="books_collections_refresh",
        ),
    )


async def delete_last_audio(state: FSMContext, callback: CallbackQuery):
    data = await state.get_data()
    msg_id = data.get("last_audio_message_id")

    if msg_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=msg_id,
            )
        except Exception:
            pass

        await state.update_data(last_audio_message_id=None)


async def send_book_excerpt(callback: CallbackQuery, state: FSMContext, book: dict):
    audio = book.get("audio") or {}
    file_id = audio.get("file_id")

    if not file_id:
        await callback.answer("У этой книги пока нет аудио-отрывка", show_alert=True)
        return

    await delete_last_audio(state, callback)

    caption = (
        "🎤🎧\n\n"
        f"<b>{book['title']}</b>\n"
        "Короткий отрывок, чтобы быстро почувствовать ритм и интонацию."
    )
    audio_type = audio.get("type")

    try:
        if audio_type == "voice":
            sent = await callback.message.answer_voice(
                voice=file_id,
                caption=caption,
                parse_mode="HTML",
            )
        elif audio_type == "audio":
            sent = await callback.message.answer_audio(
                audio=file_id,
                caption=caption,
                parse_mode="HTML",
            )
        else:
            try:
                sent = await callback.message.answer_audio(
                    audio=file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
            except Exception:
                sent = await callback.message.answer_voice(
                    voice=file_id,
                    caption=caption,
                    parse_mode="HTML",
                )
    except Exception:
        await callback.answer("Не получилось отправить отрывок. Проверь file_id аудио.", show_alert=True)
        return

    await state.update_data(last_audio_message_id=sent.message_id)
    await callback.answer("Отрывок отправлен")


async def show_book_personal_question(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("book_personal_question_ids", [])
    current_index = data.get("book_personal_question_index", 0)

    if current_index >= len(question_ids):
        await callback.answer("Вопросы закончились")
        return

    question = get_question(question_ids[current_index])
    total = len(question_ids)
    text = (
        "🧠 <b>Персональный подбор книги</b>\n\n"
        "Отвечай по ощущению. Я попробую поймать твой сегодняшний "
        "читательский настрой.\n\n"
        f"<b>{question['text']}</b>"
    )

    await replace_screen(
        callback,
        text=text,
        reply_markup=book_personal_question_keyboard(
            answers=[answer["text"] for answer in question["answers"]],
            current_index=current_index,
            total=total,
        ),
    )


async def show_personal_book_result(
    callback: CallbackQuery,
    state: FSMContext,
    user: dict,
    candidate_index: int,
):
    data = await state.get_data()
    candidates = data.get("book_personal_candidates", [])

    if candidate_index < 0 or candidate_index >= len(candidates):
        await callback.answer("Запасных вариантов больше нет", show_alert=True)
        return

    candidate = candidates[candidate_index]
    book = get_book_by_title(candidate["title"])

    if not book:
        await callback.answer("Книга не найдена", show_alert=True)
        return

    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])
    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    has_backup = candidate_index < len(candidates) - 1

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=None,
        current_source="book_personal",
        current_caption_extra=candidate["explanation"],
        personal_candidate_index=candidate_index,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])

    try:
        await callback.message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=personal_book_keyboard(
            has_backup=has_backup,
            title=book["title"],
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=candidate["explanation"],
    )


@router.callback_query(F.data == "choose_book")
async def choose_book(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.clear()
    await delete_last_audio(state, callback)

    await replace_screen(
        callback,
        text="📚 Как будем подбирать книгу?",
        reply_markup=books_mode_kb(),
    )


@router.callback_query(F.data == "books_fast")
async def books_fast(callback: CallbackQuery, user: dict, state: FSMContext):
    await state.update_data(fast_vibe_seen_count=0)
    await delete_last_audio(state, callback)
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "book")
    keyboard = book_vibe_keyboard(excluded_titles=excluded_titles)
    text = "📚 Какой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "📚 По книгам ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    sent_message = await replace_with_new_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "books_surprise")
async def books_surprise(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    book = get_random_book(
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "book"),
    )

    if not book:
        await callback.answer("Книга не найдена", show_alert=True)
        return

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=None,
        current_source="book_surprise",
        current_caption_extra=None,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])

    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=another_book_keyboard(
            vibe=None,
            title=book["title"],
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "books_personal")
async def books_personal(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    if not has_premium_access(user):
        can_use, next_available_at = free_personal_status(user)
        if not can_use and next_available_at:
            await replace_screen(
                callback,
                text=free_personal_locked_text("Персональный подбор книг", next_available_at),
                reply_markup=books_mode_kb(),
            )
            return
        consume_free_personal_use(user["telegram_id"])

    await state.set_state(BookPersonalQuiz.describing)
    await state.update_data(
        book_personal_candidates=[],
        personal_candidate_index=0,
        current_source=None,
        current_caption_extra=None,
        pending_ai_prompt=None,
    )

    await delete_tracked_message(state, callback.bot, callback.message.chat.id, "last_personal_prompt_message_id")
    prompt_message = await replace_with_new_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор книги</b>\n\n"
            "Опиши, что хочется читать: состояние, темп, сложность, "
            "нужно ли тепло, жесть, философия или польза.\n\n"
            "Например:\n"
            "<i>Хочу книгу не слишком лёгкую, но чтобы она утешала. "
            "Про одиночество, смысл и тихую надежду.</i>"
        ),
        reply_markup=book_personal_prompt_keyboard(),
    )
    if prompt_message:
        await state.update_data(last_personal_prompt_message_id=prompt_message.message_id)


@router.message(BookPersonalQuiz.describing, F.text)
async def book_personal_description(message: Message, user: dict, state: FSMContext):
    user_prompt = clean_user_text(message.text)
    await delete_tracked_message(state, message.bot, message.chat.id, "last_personal_prompt_message_id")
    state_data = await state.get_data()
    pending_ai_prompt = clean_user_text(state_data.get("pending_ai_prompt") or "")
    has_pending_ai_prompt = bool(pending_ai_prompt)
    if has_pending_ai_prompt:
        user_prompt = combine_prompt_with_clarification(pending_ai_prompt, user_prompt)
        await state.update_data(pending_ai_prompt=None)

    if len(user_prompt) < MIN_AI_PROMPT_LENGTH:
        await message.answer("Опиши чуть подробнее: настроение, сложность и чего избегаем.")
        return
    if is_too_long(user_prompt, MAX_AI_PROMPT_LENGTH):
        await message.answer(length_error_text(MAX_AI_PROMPT_LENGTH))
        return

    if not has_pending_ai_prompt:
        clarification_question = personal_clarification_question("book", user_prompt)
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

    processing_message = await message.answer("🧠 Сверяю твой вайб с базой книг...")
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    try:
        recommendations = await recommend_content_from_prompt(
            content_type="book",
            user_id=user["telegram_id"],
            user_prompt=user_prompt,
        )
    except (LLMNotConfiguredError, LLMClientError):
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=books_mode_kb(),
        )
        return

    if not recommendations:
        await state.clear()
        await processing_message.edit_text(
            ai_unavailable_text(),
            reply_markup=books_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        book_personal_candidates=[
            {
                "title": result["item"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    book = recommendations[0]["item"]
    explanation = recommendations[0]["explanation"]
    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])
    has_backup = len(recommendations) > 1

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=None,
        current_source="book_personal",
        current_caption_extra=explanation,
        personal_candidate_index=0,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])

    try:
        await processing_message.delete()
    except Exception:
        pass

    sent_message = await send_media(
        callback=message,
        item=book,
        content_type="book",
        reply_markup=personal_book_keyboard(
            has_backup=has_backup,
            title=book["title"],
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        extra_text=explanation,
    )


@router.callback_query(F.data == "books_collections")
async def books_collections(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    if not has_premium_access(user):
        await replace_screen(
            callback,
            text=premium_feature_locked_text("Premium-подборки книг"),
            reply_markup=books_mode_kb(),
        )
        return

    options = get_random_collection_names("book", count=3)
    if not options:
        await replace_screen(
            callback,
            text="💎 Premium-подборок для книг пока нет. Добавь их через /add.",
            reply_markup=books_mode_kb(),
        )
        return

    await state.update_data(book_collection_options=options)
    await show_book_collections_screen(callback, state)


@router.callback_query(F.data == "books_collections_refresh")
async def books_collections_refresh(callback: CallbackQuery, user: dict, state: FSMContext):
    if not has_premium_access(user):
        await callback.answer("Подборки доступны только в Premium", show_alert=True)
        return

    options = get_random_collection_names("book", count=3)
    await state.update_data(book_collection_options=options)
    await show_book_collections_screen(callback, state)


@router.callback_query(F.data.startswith("book_collection_pick:"))
async def book_collection_pick(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    options = data.get("book_collection_options", [])
    index = int(callback.data.split(":", 1)[1])

    if index < 0 or index >= len(options):
        await callback.answer("Подборка не найдена", show_alert=True)
        return

    collection_name = options[index]
    book = get_random_item_from_collection(
        content_type="book",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not book:
        await callback.answer("В этой подборке пока ничего нет", show_alert=True)
        return

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=None,
        current_source="book_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])

    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])
    show_next_collection = has_more_in_collection(
        "book",
        collection_name,
        user["telegram_id"],
        current_title=book["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=another_book_keyboard(
            vibe=None,
            title=book["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "next_book_collection")
async def next_book_collection(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    data = await state.get_data()
    collection_name = data.get("current_collection_name")

    if not collection_name:
        await callback.answer("Подборка уже закрыта", show_alert=True)
        return

    book = get_random_item_from_collection(
        content_type="book",
        collection_name=collection_name,
        user_id=user["telegram_id"],
    )

    if not book:
        await callback.answer("В этой подборке ты уже всё посмотрел за последнее время", show_alert=True)
        return

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=None,
        current_source="book_collection",
        current_caption_extra=None,
        current_collection_name=collection_name,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])

    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])
    show_next_collection = has_more_in_collection(
        "book",
        collection_name,
        user["telegram_id"],
        current_title=book["title"],
    )

    await callback.message.delete()
    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=another_book_keyboard(
            vibe=None,
            title=book["title"],
            collection_name=collection_name,
            show_next_collection=show_next_collection,
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
        context_note=f"💎 Подборка: <b>{collection_name}</b>",
    )


@router.callback_query(F.data == "book_personal_progress")
async def book_personal_progress(callback: CallbackQuery):
    await callback.answer("Просто выбирай вариант ниже")


@router.callback_query(BookPersonalQuiz.answering, F.data.startswith("book_personal_answer:"))
async def book_personal_answer(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    question_ids = data.get("book_personal_question_ids", [])
    current_index = data.get("book_personal_question_index", 0)
    answers_history = data.get("book_personal_answers", [])

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
        book_personal_answers=answers_history,
        book_personal_question_index=current_index,
    )

    if current_index < len(question_ids):
        await pulse_chat_action(callback)
        await show_book_personal_question(callback, state)
        return

    recommendations = recommend_books(
        user_id=user["telegram_id"],
        answer_history=answers_history,
    )

    if not recommendations:
        await state.clear()
        await replace_screen(
            callback,
            text=ai_unavailable_text(),
            reply_markup=books_mode_kb(),
        )
        return

    await state.set_state(None)
    await state.update_data(
        book_personal_candidates=[
            {
                "title": result["book"]["title"],
                "explanation": result["explanation"],
            }
            for result in recommendations[:2]
        ],
        personal_candidate_index=0,
    )

    await show_transition_screen(
        callback,
        text=(
            "🧠 <b>Персональный подбор книги</b>\n\n"
            f"{pick_phrase(BOOK_TRANSITION_LINES)}"
        ),
        action="typing",
    )
    await show_personal_book_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=0,
    )


@router.callback_query(F.data == "book_personal_backup")
async def book_personal_backup(callback: CallbackQuery, user: dict, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("personal_candidate_index", 0)

    await show_personal_book_result(
        callback=callback,
        state=state,
        user=user,
        candidate_index=current_index + 1,
    )


@router.callback_query(F.data == "listen_book_excerpt")
async def listen_book_excerpt(callback: CallbackQuery, state: FSMContext, user: dict):
    data = await state.get_data()
    book = data.get("current_item")
    content_type = data.get("current_type")

    if not book or content_type != "book":
        await callback.answer("Сначала открой карточку книги", show_alert=True)
        return

    if not has_premium_access(user):
        await callback.answer("Аудиоотрывки доступны только в Premium", show_alert=True)
        return

    await send_book_excerpt(callback, state, book)


@router.callback_query(F.data.startswith("fast_book_vibe:"))
async def book_selected(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    vibe = callback.data.split(":", 1)[1]
    book = get_random_book(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "book"),
    )

    if not book:
        await callback.answer("Книга не найдена", show_alert=True)
        return

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=vibe,
        current_source="book_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=1,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])
    show_another = has_more_in_fast_vibe(
        "book",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "book"),
    )

    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])

    await callback.message.delete()

    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=another_book_keyboard(
            vibe=vibe,
            title=book["title"],
            show_another=show_another,
            show_change_vibe=False,
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data.startswith("another_book:"))
async def another_book(callback: CallbackQuery, user: dict, state: FSMContext):
    await delete_last_audio(state, callback)

    data = await state.get_data()
    vibe = callback.data.split(":", 1)[1]
    book = get_random_book(
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "book"),
    )

    if not book:
        await books_fast(callback, user, state)
        return

    seen_count = (
        int(data.get("fast_vibe_seen_count", 1)) + 1
        if data.get("current_vibe") == vibe and data.get("current_source") == "book_fast"
        else 1
    )

    await state.update_data(
        current_item=book,
        current_type="book",
        current_vibe=vibe,
        current_source="book_fast",
        current_caption_extra=None,
        fast_vibe_seen_count=seen_count,
    )
    record_content_impression(user["telegram_id"], "book", book["title"])
    show_another = has_more_in_fast_vibe(
        "book",
        vibe,
        excluded_titles=get_recently_seen_titles(user["telegram_id"], "book"),
    )

    has_audio = bool(book.get("audio") and book["audio"].get("file_id"))
    is_fav = is_in_favorites(user["telegram_id"], "book", book["title"])
    user_rating = get_user_rating(user["telegram_id"], "book", book["title"])

    await callback.message.delete()

    sent_message = await send_media(
        callback=callback,
        item=book,
        content_type="book",
        reply_markup=another_book_keyboard(
            vibe=vibe,
            title=book["title"],
            show_another=show_another,
            show_change_vibe=seen_count >= 2,
            has_audio=has_audio,
            is_favorite=is_fav,
            user_rating=user_rating,
            is_premium=has_premium_access(user),
        ),
    )
    await track_active_screen(state, sent_message)


@router.callback_query(F.data == "refresh_book_vibes")
async def refresh_book_vibes(callback: CallbackQuery, user: dict, state: FSMContext):
    excluded_titles = get_recently_seen_titles(user["telegram_id"], "book")
    keyboard = book_vibe_keyboard(excluded_titles=excluded_titles)
    text = "📚 Какой сейчас вайб?"

    if len(keyboard.inline_keyboard) <= 2:
        text = (
            "📚 По книгам ты уже выжег все свежие вайбы за последнее время.\n\n"
            "Попробуй чуть позже, или нажми 🦉 Удиви меня."
        )

    await replace_screen(
        callback,
        text=text,
        reply_markup=keyboard,
    )
