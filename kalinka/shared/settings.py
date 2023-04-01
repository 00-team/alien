
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

# make the data dir if not exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


with open(sys.argv[1], 'r') as f:
    CONF = json.load(f)

ADMINS = CONF['admins']

DB_PATH = BASE_DIR.parent / f'twitter/data/{CONF["name"]}.shared.json'
BOT_DATA_PATH = BASE_DIR.parent / f'twitter/data/{CONF["name"]}.sdb.json'
