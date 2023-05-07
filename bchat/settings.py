
import sys
from pathlib import Path

from databases import Database
from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

from gshare import DbDict

BYTE_ORDER = 'little'
HOME_DIR = Path(__file__).parent

DATABASE_PATH = HOME_DIR / 'sqlite.db'
DATABASE_URL = 'sqlite:///' + str(DATABASE_PATH)

config = DbDict(sys.argv[1], load=True)

metadata = MetaData()
database = Database(DATABASE_URL)

BaseTable = declarative_base(metadata=metadata)
