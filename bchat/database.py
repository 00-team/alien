
from enum import Enum, auto

from databases import Database
from pydantic import BaseModel
from settings import DATABASE_URL
from sqlalchemy import Column, Integer, MetaData, String, insert, select, text
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
database = Database(DATABASE_URL)

Base = declarative_base(metadata=metadata)


class Users(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, unique=True, index=True)
    gender = Column(Integer, server_default=text('0'))
    name = Column(String, nullable=False)
    code = Column(
        Integer, autoincrement=True, unique=True,
        nullable=False, index=True
    )


class Genders(int, Enum):
    unknown = auto()
    boy = auto()
    girl = auto()


GENDER_DISPLAY = {
    Genders.unknown: 'نامعلوم',
    Genders.boy: 'پسر',
    Genders.girl: 'دختر'
}


class UserModel(BaseModel):
    user_id: int
    gender: int
    name: str
    code: int


async def add_user(user_id: int, name: str):
    query = insert(Users).values(
        user_id=user_id,
        name=name,
    )
    return await database.execute(query)


async def get_user(user_id: int = None, code: int = None):
    if not (user_id or code):
        return None

    if user_id:
        query = select(Users).where(Users.user_id == user_id)
    else:
        query = select(Users).where(Users.code == code)

    return await database.fetch_one(query)
