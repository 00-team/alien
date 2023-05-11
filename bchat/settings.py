
from pathlib import Path

from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

BYTE_ORDER = 'little'
HOME_DIR = Path(__file__).parent

DATABASE_PATH = HOME_DIR / 'sqlite.db'
DATABASE_URL = 'sqlite:///' + str(DATABASE_PATH)


AGE_RANGE = [5, 99]
NAME_RANGE = [3, 15]
KW_PROFILE = 'پروفایل من 👤'
KW_MY_LINK = 'لینک ناشناس من 🔗'


MAIN_KEYBOARD = [
    [KW_PROFILE],
    [KW_MY_LINK]
]

metadata = MetaData()

BaseTable = declarative_base(metadata=metadata)

database = Database(DATABASE_URL)
