import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.ai_profile import build_ai_profile

CONTENT_FILES = {
    "anime": Path("data/anime.json"),
    "book": Path("data/books.json"),
    "game": Path("data/games.json"),
    "movie": Path("data/movies.json"),
    "series": Path("data/series.json"),
}

PUBLIC_VIBES_PATH = Path("data/public_vibes.json")


def load_public_vibes() -> dict:
    if not PUBLIC_VIBES_PATH.exists():
        return {}

    return json.loads(PUBLIC_VIBES_PATH.read_text(encoding="utf-8"))

EMOJI_RE = re.compile(r"[^a-zа-я0-9\s/+-]+", re.I)
SPACE_RE = re.compile(r"\s+")

TYPE_DEFAULTS = {
    "anime": ["аниме", "японская анимация", "стиль", "визуальный вайб"],
    "book": ["книга", "чтение", "литература", "послевкусие"],
    "game": ["игра", "геймплей", "механика", "интерактив"],
    "movie": ["фильм", "кино", "вечерний просмотр", "визуальная история"],
    "series": ["сериал", "сезоны", "залипание", "долгое погружение"],
}

TAG_HINTS = {
    "action": ["экшен", "динамика", "адреналин"],
    "fast": ["быстрый темп", "скорость"],
    "slow": ["медленный темп", "созерцательность"],
    "dark": ["мрачный мир", "темная атмосфера"],
    "emotional": ["эмоционально", "боль", "послевкусие"],
    "romantic": ["романтика", "любовь"],
    "heartbreak": ["разбитое сердце", "слезы"],
    "comfort": ["уют", "тепло", "спокойствие"],
    "chill": ["спокойный вайб", "чилл"],
    "aesthetic": ["стиль", "атмосфера", "визуальная красота"],
    "story": ["сюжет", "сильная история"],
    "solo": ["соло", "один игрок"],
    "coop": ["кооп", "для двоих", "играть с друзьями"],
    "horror": ["хоррор", "страх"],
    "mystery": ["тайна", "загадка"],
    "mind_bending": ["ломает восприятие", "странное", "головоломка"],
    "psychological": ["психология", "давление"],
    "classic_anime": ["классика аниме", "культовое"],
    "mr600_choice": ["мистер 600 советует", "особая база"],
}

RULES = [
    (["паркур", "прыжки", "крыши", "бег по крышам", "акробатика", "скоростное перемещение"], ["паркур", "parkour", "крыш", "перекат", "акробат", "runner"]),
    (["бег", "скорость", "адреналин", "быстрый темп"], ["бег", "скорост", "быстр", "fast", "гонк", "drive"]),
    (["открытый мир", "свобода действий", "исследование", "песочница"], ["open world", "открыт", "исслед", "песочниц", "sandbox", "свобода"]),
    (["выживание", "ресурсы", "опасность", "крафт"], ["выжив", "survival", "ресурс", "крафт", "голод", "убежищ", "апокалип", "зомби"]),
    (["стелс", "скрытность", "тихий подход", "незаметность"], ["стелс", "stealth", "скрыт", "незамет", "тихо", "прят"]),
    (["шутер", "стрельба", "оружие", "перестрелки"], ["шутер", "стрель", "оруж", "перестрел", "shoot", "пушк"]),
    (["драки", "боевые искусства", "рукопашный бой", "арена"], ["драк", "бой", "бои", "ринге", "ринге", "арен", "рукопаш", "mma", "boxing"]),
    (["стратегия", "тактика", "управление", "планирование"], ["стратег", "тактик", "управл", "менедж", "планир", "resource", "республик"]),
    (["строительство", "база", "город", "ресурсный менеджмент"], ["стро", "город", "поселен", "база", "factory", "ресурс", "индустр"]),
    (["выборы и последствия", "моральный выбор", "интерактивная история"], ["выбор", "последств", "диалог", "интерактив", "решен", "telltale"]),
    (["сюжет", "сильная история", "персонажи", "эмоциональная арка"], ["сюжет", "истори", "персонаж", "геро", "драма", "story"]),
    (["атмосфера", "погружение", "вайб", "медитативность"], ["атмосфер", "погруж", "вайб", "медит", "настроен", "ambient"]),
    (["уют", "тепло", "спокойствие", "комфорт"], ["уют", "тепл", "спокой", "comfort", "chill", "мягк", "лампов"]),
    (["одиночество", "меланхолия", "тихая грусть", "внутренняя пустота"], ["одинок", "одиноч", "меланхол", "тоск", "груст", "пустот", "lonely"]),
    (["романтика", "любовь", "отношения", "нежность"], ["романт", "любов", "отношен", "нежн", "свидан", "пара", "love"]),
    (["разбитое сердце", "боль", "слезы", "эмоциональный удар"], ["разбива", "сердц", "слез", "боль", "heartbreak", "плач", "утрат"]),
    (["мотивация", "рост", "вдохновение", "сила воли"], ["мотивац", "вдохнов", "рост", "трениров", "вол", "преодол", "становлен"]),
    (["психология", "тревога", "давление", "паранойя"], ["психолог", "тревог", "давлен", "параной", "травм", "безум", "разум", "mind"]),
    (["головоломка", "интеллект", "логика", "загадка"], ["головолом", "интеллект", "логик", "загад", "puzzle", "тайн"]),
    (["детектив", "расследование", "преступление", "тайна"], ["детектив", "расслед", "преступ", "тайн", "crime", "убийств", "маньяк"]),
    (["криминал", "мафия", "бандиты", "преступный мир"], ["кримин", "мафи", "банд", "гангстер", "вор", "ограб", "преступ"]),
    (["жесть", "насилие", "кровь", "не для всех"], ["жесть", "жестк", "кров", "насил", "убий", "мяс", "без цензур"]),
    (["хоррор", "страх", "жуть", "напряжение"], ["хоррор", "ужас", "страш", "жут", "монстр", "кошмар", "horror"]),
    (["мрачный мир", "темнота", "нуар", "давящая атмосфера"], ["мрач", "темн", "нуар", "dark", "noir", "давящ"]),
    (["постапокалипсис", "конец света", "разрушенный мир"], ["постап", "апокалип", "конец свет", "зомби", "выжив", "пустош", "разруш"]),
    (["фантастика", "будущее", "технологии", "научная фантастика"], ["фантаст", "будущ", "технолог", "sci", "science fiction", "кибер", "робот"]),
    (["космос", "звезды", "планеты", "инопланетяне"], ["космос", "звезд", "планет", "space", "галакт", "иноплан", "пришел"]),
    (["киберпанк", "неон", "корпорации", "техно-антиутопия"], ["киберпанк", "cyberpunk", "неон", "корпорац", "хакер", "андроид"]),
    (["роботы", "искусственный интеллект", "человечность машины"], ["робот", "андроид", "искусствен", "ai", "машин", "меха"]),
    (["фэнтези", "магия", "мифы", "другой мир"], ["фэнтези", "маг", "миф", "дракон", "королев", "волшеб", "isekai", "исекай"]),
    (["путешествие", "дорога", "приключение", "путь героя"], ["путешеств", "дорог", "приключ", "путь", "journey", "квест"]),
    (["комедия", "юмор", "абсурд", "легкость"], ["комеди", "юмор", "смеш", "абсурд", "ирони", "сатир", "funny"]),
    (["черный юмор", "сатира", "жесткая комедия"], ["черн юмор", "сатир", "злой", "язв", "цинич"]),
    (["спорт", "соревнование", "команда", "победа"], ["спорт", "соревн", "команд", "побед", "матч", "турнир"]),
    (["школа", "учеба", "подростки", "повседневность"], ["школ", "учеб", "подрост", "студент", "универ", "school"]),
    (["семья", "дружба", "близкие", "отношения людей"], ["семь", "дружб", "близк", "родител", "дети", "друз"]),
    (["работа", "офис", "карьера", "выгорание"], ["работ", "офис", "карьер", "выгоран", "началь", "сотруд"]),
    (["деньги", "бизнес", "капитализм", "финансы"], ["деньг", "бизнес", "финанс", "капитал", "богат", "эконом"]),
    (["саморазвитие", "продуктивность", "привычки", "мышление"], ["саморазв", "продуктив", "привыч", "мышлен", "мотивац", "успех"]),
    (["научпоп", "наука", "мозг", "познание"], ["науч", "наука", "мозг", "эволюц", "космос", "физик", "биолог"]),
    (["философия", "смысл", "экзистенциальность", "вопросы жизни"], ["философ", "смысл", "экзист", "абсурд", "жизн", "смерт", "вера"]),
    (["антиутопия", "контроль", "тоталитаризм", "система"], ["антиутоп", "контрол", "тоталитар", "систем", "диктат", "наблюд", "слеж"]),
    (["классика", "культовое", "обязательная база"], ["классик", "культ", "легенд", "шедевр", "база", "must"]),
    (["русский язык", "без озвучки", "русская атмосфера"], ["русск", "росси", "снг", "москва", "питер", "озвучк"]),
    (["японский фольклор", "мистика", "духи", "медитативное"], ["япон", "фольклор", "дух", "екай", "медит", "мистик"]),
    (["милота", "кавай", "улыбка", "легкий вайб"], ["милот", "кавай", "улыб", "cute", "нежн"]),
    (["музыка", "ритм", "концерт", "звучание"], ["музык", "ритм", "концерт", "песн", "рок", "звук"]),
    (["гонки", "машины", "дорога", "скорость"], ["гонк", "машин", "авто", "дорог", "drive", "race"]),
]

TITLE_HINTS = [
    ("mirror", ["паркур", "крыши", "бег по крышам", "прыжки", "акробатика", "скорость"]),
    ("grand theft auto", ["открытый мир", "криминал", "машины", "город", "свобода действий"]),
    ("gta", ["открытый мир", "криминал", "машины", "город"]),
    ("stalker", ["зона", "чернобыль", "выживание", "мутанты", "постсоветская атмосфера"]),
    ("s.t.a.l.k.e.r", ["зона", "чернобыль", "выживание", "мутанты"]),
    ("cyberpunk", ["киберпанк", "неон", "корпорации", "будущее"]),
    ("witcher", ["фэнтези", "монстры", "моральный выбор", "славянский вайб"]),
    ("red dead", ["вестерн", "открытый мир", "лошади", "банда", "закат эпохи"]),
    ("dark souls", ["сложность", "темное фэнтези", "боссы", "умирать и учиться"]),
    ("elden ring", ["сложность", "открытый мир", "темное фэнтези", "боссы"]),
    ("portal", ["головоломка", "порталы", "логика", "черный юмор"]),
    ("disco elysium", ["диалоги", "детектив", "политика", "алкогольный нуар"]),
    ("1984", ["антиутопия", "контроль", "тоталитаризм", "слежка"]),
    ("451", ["антиутопия", "книги", "цензура", "пустота общества"]),
    ("дюна", ["пустыня", "власть", "религия", "политика", "эпик"]),
    ("dune", ["пустыня", "власть", "религия", "политика", "эпик"]),
    ("интерстеллар", ["космос", "время", "семья", "эпик", "научная фантастика"]),
    ("interstellar", ["космос", "время", "семья", "эпик"]),
]

COLLECTION_EXTRA = {
    "anime": ["закрытая подборка аниме"],
    "book": ["закрытая книжная подборка"],
    "game": ["закрытая игровая подборка"],
    "movie": ["закрытая киноподборка"],
    "series": ["закрытая сериальная подборка"],
}


def norm(text: str) -> str:
    text = (text or "").lower().replace("ё", "е")
    text = re.sub(r"[^a-zа-я0-9]+", " ", text)
    return SPACE_RE.sub(" ", text).strip()


def clean_label(text: str) -> str:
    text = (text or "").lower().replace("ё", "е")
    text = EMOJI_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    if re.fullmatch(r"[a-f0-9]{8,}", text):
        return ""
    return text


def add(tags: list[str], seen: set[str], values):
    for value in values:
        value = clean_label(str(value))
        if len(value) >= 3 and value not in seen:
            seen.add(value)
            tags.append(value)


def has_any(text: str, patterns: list[str]) -> bool:
    words = set(text.split())
    for pattern in patterns:
        pattern = pattern.lower()
        if len(pattern) <= 3:
            if pattern in words:
                return True
            continue
        if pattern in text:
            return True
    return False


def public_labels_for(content_type: str, tags: list[str], public_vibes: dict | None = None) -> list[str]:
    public_vibes = public_vibes if public_vibes is not None else load_public_vibes()
    data = public_vibes.get(content_type, {}) if isinstance(public_vibes, dict) else {}
    return [data[tag] for tag in tags if tag in data]


def split_tag_key(tag: str) -> list[str]:
    parts = tag.replace("-", "_").split("_")
    return [
        part
        for part in parts
        if len(part) >= 3
        and not part.startswith("vibe")
        and not re.fullmatch(r"[a-f0-9]{6,}", part)
    ]


def build_ai_tags(content_type: str, item: dict, public_vibes: dict | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    title = item.get("title", "")
    desc = item.get("desc", "")
    tags = item.get("tags", []) or []
    collections = item.get("premium_collections", []) or []
    platforms = item.get("platforms", []) or []
    labels = public_labels_for(content_type, tags, public_vibes=public_vibes)

    full_text = " ".join([
        title,
        desc,
        " ".join(tags),
        " ".join(labels),
        " ".join(collections),
        " ".join(platforms),
    ])
    normalized = norm(full_text)
    title_normalized = norm(title)

    add(result, seen, TYPE_DEFAULTS.get(content_type, []))

    for tag in tags:
        add(result, seen, split_tag_key(tag))
        for key, hints in TAG_HINTS.items():
            if key in tag:
                add(result, seen, hints)

    for label in labels:
        cleaned = clean_label(label)
        if cleaned:
            add(result, seen, [cleaned])

    for collection in collections:
        cleaned = clean_label(collection)
        if cleaned:
            add(result, seen, [cleaned])
        add(result, seen, COLLECTION_EXTRA.get(content_type, []))

    for platform in platforms:
        add(result, seen, [platform, f"платформа {platform}"])

    for hints, patterns in RULES:
        if has_any(normalized, patterns):
            add(result, seen, hints)

    for pattern, hints in TITLE_HINTS:
        if pattern in title_normalized or pattern in normalized:
            add(result, seen, hints)

    title_words = [
        word
        for word in norm(title).split()
        if len(word) >= 4 and not word.isdigit()
    ]
    add(result, seen, title_words[:4])

    return result[:32]


def with_ai_tags_after_public_tags(item: dict) -> dict:
    ordered = {}
    for key, value in item.items():
        if key in {"ai_tags", "ai_profile"}:
            continue
        ordered[key] = value
        if key == "tags":
            ordered["ai_tags"] = item.get("ai_tags", [])
            ordered["ai_profile"] = item.get("ai_profile", {})

    if "ai_tags" not in ordered:
        ordered["ai_tags"] = item.get("ai_tags", [])
    if "ai_profile" not in ordered:
        ordered["ai_profile"] = item.get("ai_profile", {})

    return ordered


def main():
    changed = 0
    for content_type, path in CONTENT_FILES.items():
        items = json.loads(path.read_text(encoding="utf-8"))
        for item in items:
            ai_tags = build_ai_tags(content_type, item)
            item_for_profile = {**item, "ai_tags": ai_tags}
            ai_profile = build_ai_profile(content_type, item_for_profile)
            if item.get("ai_tags") != ai_tags or item.get("ai_profile") != ai_profile:
                item["ai_tags"] = ai_tags
                item["ai_profile"] = ai_profile
                changed += 1

        ordered_items = [with_ai_tags_after_public_tags(item) for item in items]
        path.write_text(
            json.dumps(ordered_items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{content_type}: {len(items)}")

    print(f"changed: {changed}")


if __name__ == "__main__":
    main()
