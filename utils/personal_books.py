import random
from collections import defaultdict

from data.books import load_books
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_favorites, get_user_rated_content

QUESTION_COUNT = 4
ANSWER_LABELS = ["0%", "50%", "75%", "600%"]


def _answers(weight_sets: list[dict[str, float]]) -> list[dict]:
    return [
        {"text": ANSWER_LABELS[index], "weights": weights}
        for index, weights in enumerate(weight_sets)
    ]


BOOK_PERSONAL_QUESTIONS = [
    {"id": "b01", "text": "Хочется тихой книги под настроение?", "answers": _answers([{"dark": 1}, {"chill": 2, "atmospheric": 1}, {"chill": 3, "atmospheric": 2}, {"chill": 4, "atmospheric": 3}])},
    {"id": "b02", "text": "Тянет ли в темную сторону?", "answers": _answers([{"chill": 2, "classic": 1}, {"dark": 1, "deep": 1}, {"dark": 3, "dark_drama": 2}, {"dark": 4, "dark_drama": 3, "emotional": 1}])},
    {"id": "b03", "text": "Хочется ли книги, которая реально заденет?", "answers": _answers([{"classic": 1, "chill": 1}, {"emotional": 1, "deep": 1}, {"emotional": 3, "deep": 2}, {"emotional": 4, "deep": 3, "dark": 1}])},
    {"id": "b04", "text": "Нужна ли философская нота?", "answers": _answers([{"emotional": 1}, {"philosophical": 2}, {"philosophical": 3, "deep": 2}, {"philosophical": 4, "deep": 3}])},
    {"id": "b05", "text": "Хочется ли чего-то короткого и концентрированного?", "answers": _answers([{"classic": 1, "deep": 1}, {"short": 2}, {"short": 3, "deep": 1}, {"short": 4, "deep": 2}])},
    {"id": "b06", "text": "Насколько тебе сейчас нужна сложная книга, а не уютная?", "answers": _answers([{"chill": 3, "atmospheric": 1}, {"atmospheric": 2, "deep": 1}, {"deep": 3, "philosophical": 1}, {"deep": 4, "philosophical": 2, "dark_drama": 1}])},
    {"id": "b07", "text": "Есть настроение на что-то странное?", "answers": _answers([{"classic": 2}, {"weird": 2}, {"weird": 3, "deep": 1}, {"weird": 4, "philosophical": 2}])},
    {"id": "b08", "text": "Хочется классики?", "answers": _answers([{"weird": 1}, {"classic": 2}, {"classic": 3, "philosophical": 1}, {"classic": 4, "deep": 2}])},
    {"id": "b09", "text": "Нужно ли, чтобы книга оставалась в голове после чтения?", "answers": _answers([{"short": 1}, {"deep": 2, "philosophical": 1}, {"deep": 3, "philosophical": 2}, {"deep": 4, "philosophical": 3, "emotional": 1}])},
    {"id": "b10", "text": "Насколько тебе сейчас ближе одиночество, чем тепло?", "answers": _answers([{"chill": 2, "atmospheric": 1}, {"atmospheric": 2, "deep": 1}, {"dark": 2, "emotional": 1}, {"dark": 3, "emotional": 2, "deep": 1}])},
    {"id": "b11", "text": "Хочется ли прямой человеческой эмоции?", "answers": _answers([{"philosophical": 1}, {"emotional": 2}, {"emotional": 3, "deep": 1}, {"emotional": 4, "deep": 2}])},
    {"id": "b12", "text": "Нужна ли книга, которую можно прочитать быстро?", "answers": _answers([{"classic": 1, "deep": 1}, {"short": 2}, {"short": 3}, {"short": 4, "emotional": 1}])},
    {"id": "b13", "text": "Хочется ли тяжелой драмы?", "answers": _answers([{"chill": 2}, {"dark_drama": 1, "emotional": 1}, {"dark_drama": 3, "emotional": 2}, {"dark_drama": 4, "dark": 3, "emotional": 2}])},
    {"id": "b14", "text": "Насколько тебе сейчас важнее мысль, чем атмосфера?", "answers": _answers([{"atmospheric": 3}, {"atmospheric": 2, "philosophical": 1}, {"philosophical": 3, "deep": 1}, {"philosophical": 4, "deep": 2}])},
    {"id": "b15", "text": "Нужна ли лёгкая книга для выдоха?", "answers": _answers([{"dark": 2}, {"chill": 2}, {"chill": 3, "atmospheric": 1}, {"chill": 4, "short": 2, "atmospheric": 1}])},
    {"id": "b16", "text": "Хочется ли, чтобы книга была немного болезненной?", "answers": _answers([{"chill": 1}, {"emotional": 1, "dark": 1}, {"emotional": 3, "dark": 2}, {"emotional": 4, "dark_drama": 3, "deep": 1}])},
    {"id": "b17", "text": "Тебе хочется именно глубины?", "answers": _answers([{"short": 1}, {"deep": 2}, {"deep": 3, "philosophical": 1}, {"deep": 4, "philosophical": 2, "dark": 1}])},
    {"id": "b18", "text": "Есть настроение на необычную форму или странный вайб?", "answers": _answers([{"classic": 2}, {"weird": 2, "atmospheric": 1}, {"weird": 3, "deep": 1}, {"weird": 4, "philosophical": 2}])},
    {"id": "b19", "text": "Хочется ли чего-то очень знакомого и каноничного?", "answers": _answers([{"weird": 1}, {"classic": 2}, {"classic": 3, "deep": 1}, {"classic": 4, "philosophical": 2}])},
    {"id": "b20", "text": "Нужна ли медленная книга под внутренний монолог?", "answers": _answers([{"short": 2}, {"atmospheric": 2, "chill": 1}, {"atmospheric": 3, "deep": 1}, {"atmospheric": 4, "philosophical": 2, "deep": 1}])},
    {"id": "b21", "text": "Насколько тебя сейчас тянет в тень, а не в свет?", "answers": _answers([{"chill": 3}, {"atmospheric": 2, "deep": 1}, {"dark": 2, "philosophical": 1}, {"dark": 4, "dark_drama": 2}])},
    {"id": "b22", "text": "Нужно ли, чтобы книга заставляла думать о себе?", "answers": _answers([{"classic": 1}, {"deep": 2, "emotional": 1}, {"deep": 3, "philosophical": 2}, {"deep": 4, "philosophical": 3}])},
    {"id": "b23", "text": "Тянет ли к чему-то почти медитативному?", "answers": _answers([{"dark": 1}, {"chill": 2, "atmospheric": 1}, {"chill": 3, "atmospheric": 2}, {"chill": 4, "atmospheric": 3, "philosophical": 1}])},
    {"id": "b24", "text": "Нужна ли сильная авторская интонация?", "answers": _answers([{"classic": 1}, {"weird": 1, "deep": 1}, {"deep": 3, "philosophical": 1}, {"weird": 3, "deep": 2, "philosophical": 1}])},
    {"id": "b25", "text": "Насколько тебе нужна книга, которая вскроет, а не согреет?", "answers": _answers([{"chill": 3}, {"chill": 2, "emotional": 1}, {"emotional": 3, "deep": 1}, {"dark_drama": 3, "emotional": 3}])},
    {"id": "b26", "text": "Насколько тебе сейчас важнее идея, чем чувство?", "answers": _answers([{"emotional": 3}, {"emotional": 2, "philosophical": 1}, {"philosophical": 3, "deep": 1}, {"philosophical": 4, "deep": 2}])},
    {"id": "b27", "text": "Хочется ли короткого удара вместо долгого погружения?", "answers": _answers([{"deep": 1}, {"short": 2}, {"short": 3, "emotional": 1}, {"short": 4, "deep": 1}])},
    {"id": "b28", "text": "Нужен ли текст, который будет красив сам по себе?", "answers": _answers([{"short": 1}, {"atmospheric": 2}, {"atmospheric": 3, "classic": 1}, {"atmospheric": 4, "deep": 2}])},
    {"id": "b29", "text": "Хочется ли книги, где темно, но не пусто?", "answers": _answers([{"chill": 1}, {"dark": 2, "deep": 1}, {"dark": 3, "deep": 2}, {"dark": 4, "dark_drama": 2, "philosophical": 1}])},
    {"id": "b30", "text": "Нужна ли книга, которая будет казаться очень 'твоей' сегодня?", "answers": _answers([{"classic": 1}, {"deep": 2, "atmospheric": 1}, {"deep": 3, "emotional": 2}, {"deep": 4, "philosophical": 2, "weird": 1}])},
]

QUESTION_BY_ID = {question["id"]: question for question in BOOK_PERSONAL_QUESTIONS}

TAG_EXPLANATIONS = {
    "atmospheric": [
        "тебе важна не только история, но и воздух текста",
        "сегодня тебя цепляет именно настроение книги",
        "хочется раствориться в языке и атмосфере",
        "тебе важнее ощущение, чем события",
        "сейчас ты читаешь ради состояния, а не ради сюжета",
    ],

    "chill": [
        "тебе нужен более мягкий литературный режим",
        "сейчас лучше ложится спокойное чтение",
        "хочется читать без напряжения",
        "тебе нужен текст, который не давит",
        "сейчас книга должна скорее успокаивать, чем встряхивать",
    ],

    "classic": [
        "тянет к проверенным книгам",
        "сегодня хочется чего-то надежного и фундаментального",
        "хочется опереться на уже признанную литературу",
        "тебе важна классическая глубина и форма",
        "сейчас тянет к текстам, которые пережили время",
    ],

    "dark": [
        "в тебе есть запрос на темную интонацию",
        "сейчас тебя не пугает более холодный тон",
        "хочется чего-то более мрачного по настроению",
        "тебе комфортна тяжелая атмосфера",
        "сейчас ты готов к более суровому тексту",
    ],

    "dark_drama": [
        "тянет к тяжелой эмоциональной стороне",
        "сейчас ты готов к более драматичному чтению",
        "хочется прожить непростые чувства через текст",
        "тебе нужен эмоционально насыщенный конфликт",
        "сейчас ты не ищешь лёгкости, а наоборот — глубину через драму",
    ],

    "deep": [
        "тебе нужна глубина, а не просто сюжет",
        "сегодня хочется, чтобы книга проваливалась внутрь",
        "важно, чтобы текст оставлял след",
        "тебе нужно больше смыслов между строк",
        "сейчас ты ищешь не историю, а опыт",
    ],

    "emotional": [
        "тебе нужен живой эмоциональный отклик",
        "сейчас хочется, чтобы текст задевал",
        "важно что-то почувствовать во время чтения",
        "тебе нужен контакт с чувствами через книгу",
        "сейчас хочется, чтобы книга не оставляла равнодушным",
    ],

    "philosophical": [
        "тебе важно думать вместе с книгой",
        "сегодня нужен текст, который оставляет мысль",
        "хочется размышлений, а не только истории",
        "тебе нужен текст, который задаёт вопросы",
        "сейчас важнее идеи, чем события",
    ],

    "short": [
        "хочется короткого и концентрированного удара",
        "сегодня лучше работает компактное чтение",
        "тебе нужен быстрый, но насыщенный текст",
        "важно получить эффект за небольшое время",
        "сейчас формат должен быть плотным и без лишнего",
    ],

    "weird": [
        "тебе можно предложить немного странности",
        "сегодня хочется не самого очевидного текста",
        "тянет к необычным формам и идеям",
        "тебе интересны нестандартные повествования",
        "сейчас ты открыт к экспериментальному чтению",
    ],

}

EXPLANATION_OPENERS = [
    "По твоим ответам сложился очень конкретный читательский вайб.",
    "Здесь считывается не жанр, а именно твое текущее внутреннее состояние.",
    "По ответам получилось довольно точное литературное настроение.",
    "Это не случайная книга, а довольно личное попадание по состоянию.",
    "Здесь важнее не формат, а то, как книга будет ощущаться внутри.",
    "Я попытался собрать из твоих ответов не жанр, а состояние.",
    "По ответам видно, в каком ритме тебе сейчас хочется читать.",
    "Здесь скорее про настроение, чем про категорию книги.",
    "Я отталкивался от того, какой отклик тебе сейчас нужен.",
    "Твои ответы сложились в довольно ясное литературное направление.",
    "Кажется, я уловил твой читательский вайб.",
    "Похоже, сейчас тебе нужен определённый тип чтения.",
    "Твои ответы дали достаточно, чтобы сделать точный литературный выбор.",
    "Я выделил основные критерии, которые для тебя сейчас важны.",
    "Похоже, по твоим ответам можно выделить такой читательский настрой.",
    "Если опираться на твои ответы, вырисовывается примерно такая картина.",
    "Я попробовал собрать из твоих ответов общее направление.",
    "Судя по ответам, можно предположить такой вектор чтения.",
    "Интересно, но у тебя получился довольно специфичный читательский профиль.",
    "Твои ответы сложились в не самый очевидный вариант.",
    "Картина получилась немного нестандартной.",
    "Здесь вышел довольно неожиданный, но логичный результат."
]

EXPLANATION_CLOSERS = [
    "Поэтому именно эта книга сейчас выглядит самым точным попаданием.",
    "Так что из доступных вариантов именно она ложится в твой ритм лучше всего.",
    "Поэтому выбор получился не случайным, а очень собранным под тебя.",
    "Из всех вариантов именно она держит нужную тебе интонацию.",
    "В итоге она сейчас максимально точно закрывает твой читательский запрос.",
    "По ощущениям, это как раз та книга, которая тебе сейчас нужна.",
    "Поэтому именно к ней сейчас логично прийти.",
    "Судя по твоим ответам, она подходит лучше остальных.",
    "Именно она сейчас совпадает с тем, что тебе хочется прочитать.",
    "Так что это не случайный выбор — она действительно в твоём поле.",
    "Короче, это прям твоя книга сейчас.",
    "Если коротко — это оно.",
    "Тут очень чёткое совпадение с твоим настроением.",
    "Очень похоже на идеальный матч под тебя.",
    "Почти стопроцентное попадание.",
    "Это как будто под твой текущий вайб написано.",
    "Здесь всё сходится под твое состояние.",
    "Это наиболее точное совпадение по интонации и смыслу.",
    "Она аккуратно попадает в твой текущий внутренний запрос.",
    "Здесь совпадает и ритм, и содержание.",
    "Это наиболее выверенный вариант под твое состояние.",
    "По крайней мере, она сейчас выглядит самым близким вариантом.",
    "Если опираться на твои ответы, она выглядит наиболее подходящей.",
    "С большой вероятностью это именно то, что тебе сейчас зайдёт.",
    "Это, пожалуй, самый близкий вариант к тому, что ты описал.",
]


def pick_random_questions(count: int = QUESTION_COUNT) -> list[dict]:
    return random.sample(BOOK_PERSONAL_QUESTIONS, k=min(count, len(BOOK_PERSONAL_QUESTIONS)))


def get_question(question_id: str) -> dict:
    return QUESTION_BY_ID[question_id]


def accumulate_answer_weights(answer_history: list[dict]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)

    for answer in answer_history:
        answer_data = get_question(answer["question_id"])["answers"][answer["answer_index"]]
        for tag, value in answer_data["weights"].items():
            weights[tag] += value

    return dict(weights)


def build_preference_profile(user_id: int) -> tuple[dict[str, float], dict[str, float], set[str]]:
    books = load_books(include_premium_collection_only=False)
    by_title = {book["title"]: book for book in books}

    favorite_titles = {title for (title,) in get_user_favorites(user_id, "book")}
    liked_titles = set(get_user_rated_content(user_id, "book", value=1))
    disliked_titles = set(get_user_rated_content(user_id, "book", value=-1))

    positive_weights: dict[str, float] = defaultdict(float)
    negative_weights: dict[str, float] = defaultdict(float)

    for title in favorite_titles:
        book = by_title.get(title)
        if book:
            for tag in book.get("tags", []):
                positive_weights[tag] += 1.8

    for title in liked_titles:
        book = by_title.get(title)
        if book:
            for tag in book.get("tags", []):
                positive_weights[tag] += 1.2

    for title in disliked_titles:
        book = by_title.get(title)
        if book:
            for tag in book.get("tags", []):
                negative_weights[tag] += 1.3

    return dict(positive_weights), dict(negative_weights), disliked_titles | favorite_titles | liked_titles


def score_book(
    book: dict,
    answer_weights: dict[str, float],
    positive_profile: dict[str, float],
    negative_profile: dict[str, float],
) -> tuple[float, list[tuple[str, float]]]:
    tag_scores: list[tuple[str, float]] = []
    score = 0.0

    for tag in book.get("tags", []):
        tag_score = answer_weights.get(tag, 0.0)
        tag_score += positive_profile.get(tag, 0.0) * 0.8
        tag_score -= negative_profile.get(tag, 0.0) * 0.9

        if tag_score:
            tag_scores.append((tag, tag_score))
            score += tag_score

    score += random.uniform(0, 0.35)
    tag_scores.sort(key=lambda item: item[1], reverse=True)
    return score, tag_scores


def build_explanation(tag_scores: list[tuple[str, float]]) -> str:
    top_tags = [tag for tag, score in tag_scores if score > 0][:3]
    fragments = []

    for tag in top_tags:
        options = TAG_EXPLANATIONS.get(tag)
        if options:
            fragments.append(random.choice(options))

    if not fragments:
        fragments.append("тебе нужен не случайный текст, а точное попадание по внутреннему состоянию")

    opener = random.choice(EXPLANATION_OPENERS)
    closer = random.choice(EXPLANATION_CLOSERS)

    if len(fragments) == 1:
        middle = fragments[0]
    elif len(fragments) == 2:
        middle = f"{fragments[0]}, и одновременно {fragments[1]}"
    else:
        middle = f"{fragments[0]}, {fragments[1]} и {fragments[2]}"

    return f"✨ <b><i>{opener} Похоже, {middle}. {closer}</i></b>"


def recommend_books(
    user_id: int,
    answer_history: list[dict],
    excluded_titles: set[str] | None = None,
) -> list[dict]:
    books = load_books()
    answer_weights = accumulate_answer_weights(answer_history)
    positive_profile, negative_profile, blocked_titles = build_preference_profile(user_id)
    blocked_titles |= excluded_titles or set()
    blocked_titles |= get_recently_seen_titles(user_id, "book")

    scored_books = []
    fallback_books = []

    for book in books:
        if book["title"] in blocked_titles:
            continue

        score, tag_scores = score_book(book, answer_weights, positive_profile, negative_profile)
        fallback_books.append((score, tag_scores, book))

        if score > 0:
            scored_books.append((score, tag_scores, book))

    candidates = scored_books or fallback_books
    candidates.sort(key=lambda item: item[0], reverse=True)

    return [
        {
            "book": book,
            "score": score,
            "explanation": build_explanation(tag_scores),
        }
        for score, tag_scores, book in candidates[:5]
    ]
