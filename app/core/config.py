import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Setting:
    PROJECT_NAME: str = "КЦПТ расписание API"

    BASE_DIR: Path = BASE_DIR
    DATABASE_PATH: Path = BASE_DIR / "app" / "database" / "database.db"

    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    STORAGE_DIR: Path = BASE_DIR / "storage"

    SCHOOL_SHEDULE_SITE: str = os.getenv("SCHOOL_SCHEDULE_SITE")

    if SCHOOL_SHEDULE_SITE is None:
        raise ValueError("Невозможно запустить программу без указав ссылку на КЦПТ сайт")


setting = Setting()

setting.STORAGE_DIR.mkdir(parents=True, exist_ok=True)