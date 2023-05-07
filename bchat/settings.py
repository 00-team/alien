
from pathlib import Path

from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

BYTE_ORDER = 'little'
HOME_DIR = Path(__file__).parent

DATABASE_PATH = HOME_DIR / 'sqlite.db'
DATABASE_URL = 'sqlite:///' + str(DATABASE_PATH)


metadata = MetaData()
database = Database(DATABASE_URL)

BaseTable = declarative_base(metadata=metadata)
