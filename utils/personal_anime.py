import random
from collections import Counter, defaultdict

from data.anime import load_anime
from utils.content_history import get_recently_seen_titles
from utils.db import get_user_favorites, get_user_rated_content
from utils.public_vibes import get_public_vibes

QUESTION_COUNT = 4
ANSWER_LABELS = ["0%", "50%", "75%", "600%"]
ANIME_PUBLIC_VIBES = get_public_vibes("anime")
ANIME_TAG_FREQUENCY = Counter(
    tag
    for item in load_anime(include_premium_collection_only=False)
    for tag in item.get("tags", [])
)


def _answers(weight_sets: list[dict[str, float]]) -> list[dict]:
    return [
        {"text": ANSWER_LABELS[index], "weights": weights}
        for index, weights in enumerate(weight_sets)
    ]


ANIME_PERSONAL_QUESTIONS = [
    {
        "id": "a01",
        "text": "Насколько тебе нужен более тёмный аниме-вечер?",
        "answers": _answers([
            {"comfort": 2, "chill": 2},
            {"mystery": 2, "dark": 1},
            {"dark": 3, "psychological": 2},
            {"dark": 4, "psychological": 3, "vibe_7cb0843769d7": 2},
        ]),
    },
    {
        "id": "a02",
        "text": "Хочется ли, чтобы после просмотра внутри что-то треснуло?",
        "answers": _answers([
            {"action": 2, "adventure": 1},
            {"emotional": 2},
            {"emotional": 3, "heartbreak": 2},
            {"heartbreak": 4, "emotional": 3, "vibe_68b3caa45e2c": 2},
        ]),
    },
    {
        "id": "a03",
        "text": "Нужен ли драйв важнее атмосферы?",
        "answers": _answers([
            {"chill": 2, "aesthetic": 1},
            {"adventure": 2, "action": 1},
            {"action": 3, "power_growth": 2},
            {"action": 4, "power_growth": 3},
        ]),
    },
    {
        "id": "a04",
        "text": "Насколько тебе сегодня хочется уюта?",
        "answers": _answers([
            {"dark": 2, "gore": 1},
            {"comfort": 2},
            {"comfort": 3, "chill": 2},
            {"comfort": 4, "chill": 3, "vibe_dfcfa4aab9de": 2},
        ]),
    },
    {
        "id": "a05",
        "text": "Тянет ли тебя сегодня к загадке и интеллекту?",
        "answers": _answers([
            {"romantic": 1, "school_life": 1},
            {"mystery": 2, "mind_bending": 1},
            {"mystery": 3, "mind_bending": 2, "psychological": 1},
            {"mystery": 4, "mind_bending": 3, "psychological": 2},
        ]),
    },
    {
        "id": "a06",
        "text": "Нужен ли вайб пути, путешествия и большого мира?",
        "answers": _answers([
            {"psychological": 1, "school_life": 1},
            {"adventure": 2},
            {"adventure": 3, "isekai": 2},
            {"adventure": 4, "isekai": 2, "vibe_7889f9b88de1": 2},
        ]),
    },
    {
        "id": "a07",
        "text": "Насколько тебе зайдёт что-то странное, но гениальное?",
        "answers": _answers([
            {"classic_anime": 2},
            {"weird": 2, "aesthetic": 1},
            {"weird": 3, "mind_bending": 2},
            {"weird": 4, "mind_bending": 3, "vibe_d9e45276d3cd": 2},
        ]),
    },
    {
        "id": "a08",
        "text": "Хочется ли романтической ноты, а не только сюжета?",
        "answers": _answers([
            {"action": 2},
            {"romantic": 2},
            {"romantic": 3, "emotional": 2},
            {"romantic": 4, "emotional": 2, "school_life": 1},
        ]),
    },
    {
        "id": "a09",
        "text": "Нужна ли история, о которой потом ещё подумаешь?",
        "answers": _answers([
            {"chill": 2},
            {"philosophical": 2},
            {"philosophical": 3, "mystery": 1},
            {"philosophical": 4, "psychological": 2, "mind_bending": 1},
        ]),
    },
    {
        "id": "a10",
        "text": "Насколько тебе сейчас нужен импульс роста и становления?",
        "answers": _answers([
            {"comfort": 1, "chill": 1},
            {"inspiring": 2, "power_growth": 1},
            {"inspiring": 3, "power_growth": 2},
            {"inspiring": 4, "power_growth": 3, "vibe_96f2cdb1613a": 2},
        ]),
    },
    {
        "id": "a11",
        "text": "Тянет ли в знакомое детское тепло, а не в новое и острое?",
        "answers": _answers([
            {"weird": 2},
            {"nostalgic": 2, "classic_anime": 1},
            {"nostalgic": 3, "classic_anime": 2},
            {"nostalgic": 4, "classic_anime": 2, "vibe_c787198a54ac": 3},
        ]),
    },
    {
        "id": "a12",
        "text": "Насколько тебе близок спокойный ритм?",
        "answers": _answers([
            {"action": 2, "dark": 1},
            {"chill": 2},
            {"chill": 3, "comfort": 2},
            {"chill": 4, "comfort": 2, "nostalgic": 1},
        ]),
    },
    {
        "id": "a13",
        "text": "Готов ли ты к психологическому давлению и внутренней тяжести?",
        "answers": _answers([
            {"comfort": 2, "romantic": 1},
            {"psychological": 2},
            {"psychological": 3, "dark": 1},
            {"psychological": 4, "dark": 2, "mind_bending": 1},
        ]),
    },
    {
        "id": "a14",
        "text": "Хочется ли света после просмотра, а не тяжести?",
        "answers": _answers([
            {"dark": 2, "gore": 1},
            {"inspiring": 2},
            {"inspiring": 3, "comfort": 1},
            {"inspiring": 4, "comfort": 2, "power_growth": 1},
        ]),
    },
    {
        "id": "a15",
        "text": "Насколько важен красивый мир и стиль сами по себе?",
        "answers": _answers([
            {"action": 1},
            {"aesthetic": 2},
            {"aesthetic": 3, "weird": 1},
            {"aesthetic": 4, "weird": 2, "vibe_68b3caa45e2c": 1},
        ]),
    },
    {
        "id": "a16",
        "text": "Эмоциональный удар сейчас важнее экшена?",
        "answers": _answers([
            {"action": 3},
            {"emotional": 2},
            {"emotional": 3, "heartbreak": 2},
            {"emotional": 4, "heartbreak": 3, "vibe_489a0a9fa161": 1},
        ]),
    },
    {
        "id": "a17",
        "text": "Насколько тебе сейчас близок школьный вайб и жизнь между уроками?",
        "answers": _answers([
            {"dark": 1, "psychological": 1},
            {"school_life": 2},
            {"school_life": 3, "romantic": 1},
            {"school_life": 4, "romantic": 2, "vibe_85b8adbdcfaf": 1},
        ]),
    },
    {
        "id": "a18",
        "text": "Хочется ли духа соревнования и спортивного азарта?",
        "answers": _answers([
            {"philosophical": 1, "comfort": 1},
            {"sports": 2},
            {"sports": 3, "power_growth": 2},
            {"sports": 4, "power_growth": 2, "inspiring": 2},
        ]),
    },
    {
        "id": "a19",
        "text": "Нужен ли другой мир, шанс начать заново или вторая попытка?",
        "answers": _answers([
            {"realistic": 0},
            {"isekai": 2, "adventure": 1},
            {"isekai": 3, "adventure": 2, "vibe_1c45e21a7a79": 2},
            {"isekai": 4, "adventure": 2, "vibe_1c45e21a7a79": 3},
        ]),
    },
    {
        "id": "a20",
        "text": "Тянет ли тебя в более взрослый и серьёзный тон?",
        "answers": _answers([
            {"school_life": 1, "romantic": 1},
            {"philosophical": 2},
            {"dark": 2, "philosophical": 2},
            {"dark": 3, "philosophical": 3, "psychological": 1},
        ]),
    },
    {
        "id": "a21",
        "text": "Нужен ли тайтл, который быстро захватит и не отпустит?",
        "answers": _answers([
            {"chill": 2},
            {"mystery": 2},
            {"action": 2, "mystery": 2},
            {"action": 3, "mystery": 3, "mind_bending": 1},
        ]),
    },
    {
        "id": "a22",
        "text": "Хочется ли красоты вперемешку с грустью?",
        "answers": _answers([
            {"action": 1},
            {"nostalgic": 2, "aesthetic": 1},
            {"nostalgic": 3, "emotional": 1, "aesthetic": 2},
            {"nostalgic": 4, "heartbreak": 2, "vibe_68b3caa45e2c": 2},
        ]),
    },
    {
        "id": "a23",
        "text": "Жесть и без цензуры сейчас скорее плюс, чем минус?",
        "answers": _answers([
            {"comfort": 2},
            {"dark": 2, "gore": 1},
            {"gore": 3, "dark": 2},
            {"gore": 4, "dark": 2, "vibe_58ea48f24f25": 2, "vibe_d9e45276d3cd": 1},
        ]),
    },
    {
        "id": "a24",
        "text": "Хочется ли чего-то легендарного по статусу?",
        "answers": _answers([
            {"weird": 1},
            {"classic_anime": 2},
            {"classic_anime": 3, "action": 1},
            {"classic_anime": 4, "philosophical": 1, "nostalgic": 1},
        ]),
    },
    {
        "id": "a25",
        "text": "Нужен ли более мягкий, мечтательный или немного сонный тон?",
        "answers": _answers([
            {"psychological": 1, "dark": 1},
            {"comfort": 2, "romantic": 1},
            {"romantic": 3, "comfort": 2, "weird": 1},
            {"romantic": 4, "comfort": 2, "weird": 2},
        ]),
    },
    {
        "id": "a26",
        "text": "Насколько тебе зайдёт хаос и беспорядок вместо аккуратного сюжета?",
        "answers": _answers([
            {"comfort": 2},
            {"weird": 2, "action": 1},
            {"weird": 3, "action": 2, "vibe_d9e45276d3cd": 2},
            {"weird": 4, "action": 2, "vibe_d9e45276d3cd": 3},
        ]),
    },
    {
        "id": "a27",
        "text": "Нужен ли вайб семьи с секретами и двойной жизни?",
        "answers": _answers([
            {"action": 1},
            {"mystery": 2},
            {"mystery": 3, "romantic": 1},
            {"mystery": 4, "vibe_ca4967ea88a5": 3, "romantic": 1},
        ]),
    },
    {
        "id": "a28",
        "text": "Тянет ли к сцене, музыке и творческому нерву?",
        "answers": _answers([
            {"dark": 1},
            {"emotional": 2, "school_life": 1},
            {"emotional": 3, "vibe_85b8adbdcfaf": 2},
            {"emotional": 4, "vibe_489a0a9fa161": 2, "vibe_85b8adbdcfaf": 2},
        ]),
    },
    {
        "id": "a29",
        "text": "Нужна ли история про что-то чужое внутри человека?",
        "answers": _answers([
            {"comfort": 2},
            {"psychological": 2},
            {"psychological": 3, "gore": 1},
            {"psychological": 4, "gore": 2, "vibe_e1af870bf063": 3},
        ]),
    },
    {
        "id": "a30",
        "text": "Хочется ли скорости, резкости и чувства, что всё уже понеслось?",
        "answers": _answers([
            {"chill": 2},
            {"action": 2},
            {"action": 3, "sports": 1},
            {"action": 4, "sports": 1, "vibe_e11228c14ef2": 3},
        ]),
    },
]

QUESTION_BY_ID = {question["id"]: question for question in ANIME_PERSONAL_QUESTIONS}

TAG_EXPLANATIONS = {
    "action": [
        "тебе нужен темп и мощный импульс",
        "сейчас тебе важно движение, а не долгое раскачивание",
    ],
    "dark": [
        "тебя не отпугивает тяжёлый и мрачный тон",
        "сейчас можно идти в более тёмную сторону без скидок",
    ],
    "psychological": [
        "тебя цепляет внутреннее напряжение и давление",
        "сейчас интереснее истории, которые лезут под кожу, а не просто шумят",
    ],
    "mystery": [
        "тебе нужна загадка, которая будет тянуть дальше",
        "важно чувство тайны, а не только красивый фасад",
    ],
    "mind_bending": [
        "тебе зайдёт ощущение, что почва под ногами слегка уехала",
        "сейчас хочется не прямой истории, а игры с восприятием",
    ],
    "emotional": [
        "ты готов к сильному эмоциональному попаданию",
        "сейчас может сработать история, которая бьёт по чувствам без стеснения",
    ],
    "heartbreak": [
        "тебе можно предложить что-то болезненное, но красивое",
        "сейчас внутри есть место для истории, которая ломает аккуратно, но точно",
    ],
    "comfort": [
        "тебе нужен более мягкий и безопасный тон",
        "сейчас лучше работает что-то тёплое и неагрессивное",
    ],
    "romantic": [
        "в ответах чувствуется запрос на сердечную ноту",
        "тебе сейчас подходит более чувственный и близкий вайб",
    ],
    "weird": [
        "можно зайти не в очевидное, а в странное и живое",
        "сейчас тебе интереснее что-то со сдвигом, а не просто аккуратная норма",
    ],
    "philosophical": [
        "тебе нужен не только сюжет, но и мысль внутри",
        "сейчас ты ищешь внутреннее эхо после просмотра",
    ],
    "inspiring": [
        "нужна история, которая приподнимет изнутри",
        "тебе сейчас важен импульс движения вперёд",
    ],
    "power_growth": [
        "сейчас особенно хорошо ложится история про рост и набор силы",
        "тебя тянет к траектории «из слабого в сильного»",
    ],
    "adventure": [
        "тебе нужен дух пути и ощущение большого мира",
        "сейчас хочется движения, дороги и открытия нового пространства",
    ],
    "nostalgic": [
        "тебе близко знакомое тёплое чувство",
        "сейчас ностальгия ляжет особенно мягко",
    ],
    "chill": [
        "тебе нужен плавный ритм, а не постоянный удар",
        "сейчас лучше сработает неагрессивная и атмосферная подача",
    ],
    "classic_anime": [
        "тянет к вещам со статусом и весом",
        "сейчас хочется зайти в проверенное аниме-наследие",
    ],
    "aesthetic": [
        "тебе важна не только история, но и то, как она выглядит и дышит",
        "сейчас визуальная атмосфера для тебя почти так же важна, как сюжет",
    ],
    "school_life": [
        "тебе сейчас близок школьный и повседневный нерв",
        "в этом состоянии может особенно точно лечь история про жизнь между уроками и чувствами",
    ],
    "sports": [
        "тебя может зарядить спортивный азарт и дух соревнования",
        "сейчас хорошо ложится энергия матча, роста и преодоления",
    ],
    "isekai": [
        "тебя тянет к ощущению другого мира и второго старта",
        "сейчас есть запрос на смену реальности и новую точку входа",
    ],
    "gore": [
        "тебя не пугает жесть и телесность",
        "сейчас можно позволить себе аниме без сглаженных углов",
    ],
    "vibe_c787198a54ac": [
        "в тебе явно отзывается ностальгия по детству",
    ],
    "vibe_d9e45276d3cd": [
        "сейчас тебе может зайти управляемый хаос и красивый беспорядок",
    ],
    "vibe_68b3caa45e2c": [
        "в ответах чувствуется тяга к чему-то болезненному, но красивому",
    ],
    "vibe_dfcfa4aab9de": [
        "тебе может быть нужен воздух, природа и ощущение открытого пространства",
    ],
    "vibe_85b8adbdcfaf": [
        "тебя тянет к музыке и связи, которая через неё возникает",
    ],
    "vibe_555c329f8241": [
        "сейчас хорошо ложится энергия противостояния всем вокруг",
    ],
    "vibe_fb3f395ebe30": [
        "ты не избегаешь истории с настоящей ямой отчаяния",
    ],
    "vibe_e1af870bf063": [
        "тебе может откликнуться история про что-то чужое внутри человека",
    ],
    "vibe_96f2cdb1613a": [
        "тебя цепляет траектория «стать героем, даже если ты обычный»",
    ],
    "vibe_1c45e21a7a79": [
        "в ответах есть явная тяга ко второй попытке и новому заходу в жизнь",
    ],
    "vibe_ca4967ea88a5": [
        "тебя может зацепить тема семьи, в которой слишком много секретов",
    ],
    "vibe_489a0a9fa161": [
        "сейчас хорошо ложится нерв сцены и столкновения образа с реальностью",
    ],
    "vibe_5d9ad9172a53": [
        "тебе может откликнуться история про обучение человечности",
    ],
    "vibe_58ea48f24f25": [
        "ты не избегаешь жёсткой, почти костяной телесности",
    ],
    "vibe_e11228c14ef2": [
        "тебя может подхватить скорость и азарт гонки",
    ],
    "vibe_7889f9b88de1": [
        "внутри есть запрос на свободу, море и путь без поводка",
    ],
    "vibe_7cb0843769d7": [
        "тебя может зацепить история про право на силу и моральную трещину внутри",
    ],
}

EXPLANATION_OPENERS = [
    "Твой набор ответов сложился в довольно читаемый аниме-запрос.",
    "По ответам вырисовался не случайный вкус, а вполне точное состояние.",
    "Я попытался поймать не жанр, а твой текущий аниме-ритм.",
    "Здесь считывается не просто настроение, а уже довольно конкретный запрос к истории.",
]

EXPLANATION_CLOSERS = [
    "Поэтому именно это аниме сейчас выглядит самым естественным попаданием.",
    "Так что из доступных вариантов именно оно ложится точнее всего.",
    "Поэтому выбор здесь получился не случайный, а вполне личный.",
    "Так что сейчас именно оно должно сработать сильнее остальных.",
]


def pick_random_questions(count: int = QUESTION_COUNT) -> list[dict]:
    return random.sample(
        ANIME_PERSONAL_QUESTIONS,
        k=min(count, len(ANIME_PERSONAL_QUESTIONS)),
    )


def get_question(question_id: str) -> dict:
    return QUESTION_BY_ID[question_id]


def accumulate_answer_weights(answer_history: list[dict]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)

    for answer in answer_history:
        answer_data = get_question(answer["question_id"])["answers"][answer["answer_index"]]
        for tag, value in answer_data["weights"].items():
            if value:
                weights[tag] += value

    return dict(weights)


def build_preference_profile(user_id: int) -> tuple[dict[str, float], dict[str, float], set[str]]:
    anime_list = load_anime(include_premium_collection_only=False)
    by_title = {item["title"]: item for item in anime_list}

    favorite_titles = {title for (title,) in get_user_favorites(user_id, "anime")}
    liked_titles = set(get_user_rated_content(user_id, "anime", value=1))
    disliked_titles = set(get_user_rated_content(user_id, "anime", value=-1))

    positive_weights: dict[str, float] = defaultdict(float)
    negative_weights: dict[str, float] = defaultdict(float)

    for title in favorite_titles:
        item = by_title.get(title)
        if item:
            for tag in item.get("tags", []):
                positive_weights[tag] += 1.8

    for title in liked_titles:
        item = by_title.get(title)
        if item:
            for tag in item.get("tags", []):
                positive_weights[tag] += 1.2

    for title in disliked_titles:
        item = by_title.get(title)
        if item:
            for tag in item.get("tags", []):
                negative_weights[tag] += 1.3

    return (
        dict(positive_weights),
        dict(negative_weights),
        disliked_titles | favorite_titles | liked_titles,
    )


def tag_priority_bonus(tag: str) -> float:
    count = ANIME_TAG_FREQUENCY.get(tag, 0)

    if count <= 1:
        return 0.55
    if count <= 2:
        return 0.42
    if count <= 4:
        return 0.28
    if count <= 7:
        return 0.14
    return 0.0


def score_anime(
    item: dict,
    answer_weights: dict[str, float],
    positive_profile: dict[str, float],
    negative_profile: dict[str, float],
) -> tuple[float, list[tuple[str, float]]]:
    tag_scores: list[tuple[str, float]] = []
    score = 0.0

    for tag in item.get("tags", []):
        answer_signal = answer_weights.get(tag, 0.0)
        profile_signal = positive_profile.get(tag, 0.0) * 0.8
        negative_signal = negative_profile.get(tag, 0.0) * 0.9

        tag_score = answer_signal + profile_signal - negative_signal

        if answer_signal > 0:
            tag_score += tag_priority_bonus(tag) * min(1.0, answer_signal / 3)

        if tag_score:
            tag_scores.append((tag, tag_score))
            score += tag_score

    score += random.uniform(0, 0.25)
    tag_scores.sort(key=lambda entry: entry[1], reverse=True)
    return score, tag_scores


def fallback_tag_explanation(tag: str) -> str | None:
    label = ANIME_PUBLIC_VIBES.get(tag)
    if not label:
        return None
    return f"тебя явно тянет в вайб «{label}»"


def build_explanation(tag_scores: list[tuple[str, float]]) -> str:
    top_tags = [tag for tag, score in tag_scores if score > 0][:3]
    fragments = []

    for tag in top_tags:
        options = TAG_EXPLANATIONS.get(tag)
        if options:
            fragments.append(random.choice(options))
            continue

        fallback = fallback_tag_explanation(tag)
        if fallback:
            fragments.append(fallback)

    if not fragments:
        fragments.append("тебе нужен не просто тайтл, а точное попадание в состояние")

    opener = random.choice(EXPLANATION_OPENERS)
    closer = random.choice(EXPLANATION_CLOSERS)

    if len(fragments) == 1:
        middle = fragments[0]
    elif len(fragments) == 2:
        middle = f"{fragments[0]}, и одновременно {fragments[1]}"
    else:
        middle = f"{fragments[0]}, {fragments[1]} и {fragments[2]}"

    return f"✨ <b><i>{opener} Похоже, {middle}. {closer}</i></b>"


def recommend_anime(
    user_id: int,
    answer_history: list[dict],
    excluded_titles: set[str] | None = None,
) -> list[dict]:
    anime_list = load_anime(include_premium_collection_only=False)
    answer_weights = accumulate_answer_weights(answer_history)
    positive_profile, negative_profile, blocked_titles = build_preference_profile(user_id)
    blocked_titles |= excluded_titles or set()
    blocked_titles |= get_recently_seen_titles(user_id, "anime")

    scored_items = []
    fallback_items = []

    for item in anime_list:
        if item["title"] in blocked_titles:
            continue

        score, tag_scores = score_anime(
            item,
            answer_weights,
            positive_profile,
            negative_profile,
        )
        fallback_items.append((score, tag_scores, item))

        if score > 0:
            scored_items.append((score, tag_scores, item))

    candidates = scored_items or fallback_items
    candidates.sort(key=lambda entry: entry[0], reverse=True)

    return [
        {
            "anime": item,
            "score": score,
            "explanation": build_explanation(tag_scores),
        }
        for score, tag_scores, item in candidates[:5]
    ]
