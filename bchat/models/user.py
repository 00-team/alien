
from enum import Enum, auto

from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import JSON, Column, Integer, String, text


class Users(BaseTable):
    __tablename__ = 'users'

    row_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    gender = Column(Integer, nullable=False, server_default=text('0'))
    age = Column(Integer, nullable=False, server_default=text('20'))
    direct_msg_id = Column(Integer)
    block_list = Column(JSON, server_default='[]')


class Genders(int, Enum):
    unknown = 0
    boy = auto()
    girl = auto()


class UserModel(BaseModel):
    row_id: int
    user_id: int
    gender: Genders
    name: str
    age: int
    direct_msg_id: int = None
    block_list: list[int] = []


GENDER_DISPLAY = {
    Genders.unknown: 'نامعلوم 👤',
    Genders.boy: 'پسر 👨',
    Genders.girl: 'دختر 👩'
}


gender_keys = [g.value for g in Genders.__members__.values()]
gender_pattern = '|'.join((str(g) for g in gender_keys))
