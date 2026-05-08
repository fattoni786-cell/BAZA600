import json
import random
from pathlib import Path

DATA_PATH = Path("data/series.json")


def load_series():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_random_series(tag: str):
    series = load_series()
    filtered = [s for s in series if tag in s.get("tags", [])]
    return random.choice(filtered if filtered else series)
