from datetime import datetime
from pathlib import Path
from shutil import copy2

from utils.db import DB_PATH

DATA_DIR = Path("data")
BACKUP_DIR = Path("backups")
BACKUP_KEEP_DAYS = 14


def create_daily_backup() -> Path | None:
    if not DATA_DIR.exists():
        return None

    today = datetime.now().strftime("%Y-%m-%d")
    backup_path = BACKUP_DIR / today
    marker = backup_path / ".done"

    if marker.exists():
        return backup_path

    backup_path.mkdir(parents=True, exist_ok=True)

    for path in DATA_DIR.glob("*.json"):
        copy2(path, backup_path / path.name)

    if DB_PATH.exists():
        copy2(DB_PATH, backup_path / DB_PATH.name)

    marker.write_text(datetime.now().isoformat(), encoding="utf-8")
    cleanup_old_backups()
    return backup_path


def create_snapshot_backup(label: str = "snapshot") -> Path | None:
    if not DATA_DIR.exists():
        return None

    safe_label = "".join(
        char for char in label.lower().replace(" ", "_")
        if char.isalnum() or char in "_-"
    ) or "snapshot"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = BACKUP_DIR / f"{timestamp}_{safe_label}"
    backup_path.mkdir(parents=True, exist_ok=True)

    for path in DATA_DIR.glob("*.json"):
        copy2(path, backup_path / path.name)

    if DB_PATH.exists():
        copy2(DB_PATH, backup_path / DB_PATH.name)

    return backup_path


def cleanup_old_backups():
    if not BACKUP_DIR.exists():
        return

    backups = [
        path
        for path in BACKUP_DIR.iterdir()
        if path.is_dir()
    ]
    backups.sort(key=lambda path: path.name, reverse=True)

    for old_backup in backups[BACKUP_KEEP_DAYS:]:
        for child in old_backup.iterdir():
            child.unlink()
        old_backup.rmdir()
