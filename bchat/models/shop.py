
from enum import Enum

from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import JSON, Boolean, Column, Integer, String, text


class ShopTable(BaseTable):
    __tablename__ = 'shop'

    item_id = Column(
        Integer, primary_key=True,
        autoincrement=True, index=True
    )
    user_id = Column(Integer, index=True)
    score = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    item_type = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    done = Column(Boolean, server_default=text('0'))


class ItemType(int, Enum):
    charge = 0
    member = 1


class ShopModel(BaseModel):
    item_id: int
    user_id: int
    score: int
    reason: str
    item_type: ItemType
    data: dict
    done: bool = False


class ChargcTable(BaseTable):
    __tablename__ = 'charge_code'

    cc_id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer, nullable=False)
    user_id = Column(Integer)
    op = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    used = Column(Boolean, server_default=text('0'))


class ChargcModel(BaseModel):
    cc_id: int
    amount: int
    user_id: int = None
    op: str
    code: str
    used: bool = False
