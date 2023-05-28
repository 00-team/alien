
from enum import Enum, auto

from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import JSON, Column, Integer, String, text


class Users(BaseTable):
    __tablename__ = 'users'

    # row_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, primary_key=True, unique=True, index=True)
    codename = Column(String, nullable=False, index=True, unique=True)
    name = Column(String, nullable=False)
    gender = Column(Integer, nullable=False, server_default=text('0'))
    age = Column(Integer, nullable=False, server_default=text('20'))
    direct_msg_id = Column(Integer)
    block_list = Column(JSON, server_default='{}')
    saved_list = Column(JSON, server_default='{}')
    invite_score = Column(Integer, server_default=text('0'))


class Genders(int, Enum):
    unknown = 0
    boy = auto()
    girl = auto()


class UserModel(BaseModel):
    user_id: int
    codename: str
    gender: Genders
    name: str
    age: int
    direct_msg_id: int = None
    block_list: dict = {}
    saved_list: dict = {}
    invite_score: int = 0
    new_user: bool = False


GENDER_DISPLAY = {
    Genders.unknown: 'نامعلوم 👤',
    Genders.boy: 'پسر 👨',
    Genders.girl: 'دختر 👩'
}


gender_keys = [g.value for g in Genders.__members__.values()]
gender_pattern = '|'.join((str(g) for g in gender_keys))
