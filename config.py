from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATABASE_NAME = "market.db"

DATABASE_PATH = BASE_DIR / DATABASE_NAME

LOG_FOLDER = BASE_DIR / "logs"

EXPORT_FOLDER = BASE_DIR / "exports"

DATA_FOLDER = BASE_DIR / "data"

LOG_FOLDER.mkdir(exist_ok=True)

EXPORT_FOLDER.mkdir(exist_ok=True)