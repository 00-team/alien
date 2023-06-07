
from pathlib import Path

from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

BYTE_ORDER = 'little'
HOME_DIR = Path(__file__).parent

DEF_PHOTO = HOME_DIR / 'default.jpeg'

DATABASE_PATH = HOME_DIR / 'sqlite.db'
DATABASE_URL = 'sqlite:///' + str(DATABASE_PATH)


CODE_CHANGE_COST = 100
NAME_CHANGE_COST = 3
PICTURE_CHANGE_COST = 5

AGE_RANGE = [5, 99]
NAME_RANGE = [3, 15]
KW_PROFILE = 'پروفایل من 👤'
KW_MY_LINK = 'لینک ناشناس من 🔗'
KW_DRTNSEN = 'پیام های خوانده نشده 📬'
KW_SAVELST = 'کاربران ذخیره شده 📋'


MAIN_KEYBOARD = [
    [KW_PROFILE],
    [KW_MY_LINK, KW_SAVELST],
    [KW_DRTNSEN],
]

metadata = MetaData()

BaseTable = declarative_base(metadata=metadata)

sqlx = Database(DATABASE_URL)
database = sqlx
