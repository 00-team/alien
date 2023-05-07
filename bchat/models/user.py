
from enum import Enum, auto

from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import Column, Integer, String, text


class Users(BaseTable):
    __tablename__ = 'users'

    row_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    gender = Column(Integer, server_default=text('0'))
    age = Column(Integer, server_default=text('20'))


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


GENDER_DISPLAY = {
    Genders.unknown: 'نامعلوم',
    Genders.boy: 'پسر',
    Genders.girl: 'دختر'
}
