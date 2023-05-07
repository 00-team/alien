from databases import Database
from settings import DATABASE_URL
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

metadata = MetaData()
database = Database(DATABASE_URL)


users = Table(
    'users',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('gender', String),
    Column('name', String, nullable=False),
    Column('code', String, nullable=False, unique=True),
)


# engine = create_engine(DATABASE_URL)
