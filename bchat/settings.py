
from pathlib import Path

BYTE_ORDER = 'little'
HOME_DIR = Path(__file__).parent

DATABASE_PATH = HOME_DIR / 'sqlite.db'
DATABASE_URL = 'sqlite:///' + str(DATABASE_PATH)
