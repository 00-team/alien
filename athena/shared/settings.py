
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'

# make the data dir if not exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_DB_PATH = DATA_DIR / 'users.json'
CHANNEL_DB_PATH = DATA_DIR / 'channels.json'
GENERAL_DB_PATH = DATA_DIR / 'generals.json'


EXPIRE_TIME = 15 * 60
FORWARD_DELAY = 10 * 60


with open(sys.argv[1], 'r') as f:
    CONF = json.load(f)
