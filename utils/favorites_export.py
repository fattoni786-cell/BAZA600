import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from data.anime import load_anime
from data.books import load_books
from data.games import load_games
from data.movies import load_movies
from data.series import load_series

CONTENT_LOADERS = {
    "anime": load_anime,
    "book": load_books,
    "game": load_games,
    "movie": load_movies,
    "series": load_series,
}

CONTENT_TITLES = {
    "anime": "Аниме",
    "book": "Книги",
    "game": "Игры",
    "movie": "Фильмы",
    "series": "Сериалы",
}

CONTENT_ORDER = ["anime", "book", "game", "movie", "series"]

IMAGE_STYLE_TITLES = {
    "minimal": "Минималистичный",
    "colorful": "Красочный и яркий",
    "warm": "Тёплый и милый",
}

FONT_SEGOE = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_SEGOE_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
FONT_TREBUCHET = Path(r"C:\Windows\Fonts\trebuc.ttf")
FONT_TREBUCHET_BOLD = Path(r"C:\Windows\Fonts\trebucbd.ttf")
FONT_GEORGIA = Path(r"C:\Windows\Fonts\georgia.ttf")
FONT_GEORGIA_BOLD = Path(r"C:\Windows\Fonts\georgiab.ttf")
FONT_GABRIOLA = Path(r"C:\Windows\Fonts\Gabriola.ttf")


def collect_favorites_by_type(
    rows: list[tuple],
    selected_types: list[str] | None = None,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    selected_set = set(selected_types or CONTENT_ORDER)

    if not rows:
        return grouped

    if len(rows[0]) == 2:
        by_type: dict[str, set[str]] = {}
        for content_type, content_id in rows:
            by_type.setdefault(content_type, set()).add(content_id)
    else:
        raise ValueError("Expected favorites rows in (content_type, content_id) format")

    for content_type in CONTENT_ORDER:
        if content_type not in selected_set:
            continue

        titles = by_type.get(content_type)
        if not titles:
            continue

        items = CONTENT_LOADERS[content_type]()
        grouped[content_type] = [
            item["title"]
            for item in items
            if item["title"] in titles
        ]

    return grouped


def build_favorites_text(rows: list[tuple], selected_types: list[str] | None = None) -> str:
    grouped = collect_favorites_by_type(rows, selected_types=selected_types)
    total = sum(len(items) for items in grouped.values())

    lines = [
        "⭐ <b>Избранное в Базе №600</b>",
        "",
        f"Всего сохранено: <b>{total}</b>",
    ]

    for content_type in CONTENT_ORDER:
        items = grouped.get(content_type)
        if not items:
            continue

        lines.append("")
        lines.append(f"<b>{CONTENT_TITLES[content_type]} ({len(items)})</b>")
        for index, title in enumerate(items, 1):
            lines.append(f"{index}. {title}")

    return "\n".join(lines)


def _load_font(path: Path, size: int):
    try:
        return ImageFont.truetype(str(path), size=size)
    except Exception:
        return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _get_style_palette(style: str) -> dict:
    if style == "colorful":
        return {
            "bg": "#F4FBFF",
            "card": "#FFFFFF",
            "accent": "#0E7490",
            "secondary": "#475569",
            "divider": "#7DD3FC",
            "section_bg": "#E0F2FE",
            "section_text": "#075985",
            "font_regular": FONT_TREBUCHET,
            "font_bold": FONT_TREBUCHET_BOLD,
            "title_font": FONT_TREBUCHET_BOLD,
        }
    if style == "warm":
        return {
            "bg": "#FFF6ED",
            "card": "#FFFBF7",
            "accent": "#9A3412",
            "secondary": "#7C5E57",
            "divider": "#F4A261",
            "section_bg": "#FDE6D6",
            "section_text": "#7C2D12",
            "font_regular": FONT_GEORGIA,
            "font_bold": FONT_GEORGIA_BOLD,
            "title_font": FONT_GABRIOLA,
        }
    return {
        "bg": "#F5F0E8",
        "card": "#FBF8F3",
        "accent": "#1B2430",
        "secondary": "#5C6773",
        "divider": "#D8CFC2",
        "section_bg": "#EFE7DB",
        "section_text": "#1B2430",
        "font_regular": FONT_SEGOE,
        "font_bold": FONT_SEGOE_BOLD,
        "title_font": FONT_SEGOE_BOLD,
    }


def render_favorites_image(
    rows: list[tuple],
    selected_types: list[str] | None = None,
    style: str = "minimal",
) -> str:
    grouped = collect_favorites_by_type(rows, selected_types=selected_types)
    total = sum(len(items) for items in grouped.values())
    palette = _get_style_palette(style)

    width = 1080
    padding_x = 80
    top = 80
    line_gap = 14
    section_gap = 28
    max_text_width = width - (padding_x * 2)

    title_font_size = 54 if style != "warm" else 72
    title_font = _load_font(palette["title_font"], title_font_size)
    subtitle_font = _load_font(palette["font_regular"], 28)
    section_font = _load_font(palette["font_bold"], 32)
    item_font = _load_font(palette["font_regular"], 26)

    measure_img = Image.new("RGB", (width, 100), palette["bg"])
    draw = ImageDraw.Draw(measure_img)

    height = top + 140
    for content_type in CONTENT_ORDER:
        items = grouped.get(content_type)
        if not items:
            continue

        height += 62
        for index, title in enumerate(items, 1):
            wrapped = _wrap_text(draw, f"{index}. {title}", item_font, max_text_width)
            height += (len(wrapped) * 34) + line_gap
        height += section_gap

    height += 60

    image = Image.new("RGB", (width, height), palette["bg"])
    draw = ImageDraw.Draw(image)

    accent = palette["accent"]
    secondary = palette["secondary"]
    divider = palette["divider"]

    draw.rounded_rectangle(
        (36, 36, width - 36, height - 36),
        radius=32,
        fill=palette["card"],
        outline=divider,
        width=3,
    )

    y = top
    draw.text((padding_x, y), "Избранное в Базе №600", font=title_font, fill=accent)
    y += 86 if style == "warm" else 74
    draw.text(
        (padding_x, y),
        f"Сохранено тайтлов: {total}",
        font=subtitle_font,
        fill=secondary,
    )
    y += 52
    draw.line((padding_x, y, width - padding_x, y), fill=divider, width=3)
    y += 36

    for content_type in CONTENT_ORDER:
        items = grouped.get(content_type)
        if not items:
            continue

        header = f"{CONTENT_TITLES[content_type]} ({len(items)})"
        header_bbox = draw.textbbox((0, 0), header, font=section_font)
        header_width = header_bbox[2] - header_bbox[0]
        draw.rounded_rectangle(
            (padding_x - 8, y - 8, padding_x + header_width + 24, y + 38),
            radius=18,
            fill=palette["section_bg"],
        )
        draw.text(
            (padding_x + 6, y - 1),
            header,
            font=section_font,
            fill=palette["section_text"],
        )
        y += 48

        for index, title in enumerate(items, 1):
            wrapped = _wrap_text(draw, f"{index}. {title}", item_font, max_text_width)
            for line in wrapped:
                draw.text((padding_x, y), line, font=item_font, fill=accent)
                y += 34
            y += line_gap

        y += section_gap

    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp.close()
    image.save(temp.name, format="PNG")
    return temp.name
