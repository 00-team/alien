
from enum import Enum

from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import JSON, Boolean, Column, Integer, String, text


class ShopTable(BaseTable):
    __tablename__ = 'shop'

    user_id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    item = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    done = Column(Boolean, server_default=text('0'))


class ItemType(int, Enum):
    phone_charge = 0
    channel_member = 1


class ShopModel(BaseModel):
    user_id: int
    score: int
    reason: str
    item: ItemType
    data: dict
    done: bool = False
