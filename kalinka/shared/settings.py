
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

# make the data dir if not exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / 'database.json'
BOT_DATA_PATH = DATA_DIR / 'bot_data.json'

ADMINS = []

with open(BASE_DIR / 'tel.token') as f:
    TOKEN = f.read()
