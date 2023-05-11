
from pydantic import BaseModel
from settings import BaseTable
from sqlalchemy import Boolean, Column, Integer, text


class Direct(BaseTable):
    __tablename__ = 'direct'

    direct_id = Column(
        Integer, primary_key=True,
        autoincrement=True, index=True
    )
    user_id = Column(Integer, index=True, nullable=False)
    sender_id = Column(Integer, index=True, nullable=False)
    message_id = Column(Integer, nullable=False)
    reply_to = Column(Integer)
    seen = Column(Boolean, server_default=text('0'))


class DirectModel(BaseModel):
    direct_id: int
    user_id: int
    sender_id: int
    message_id:  int
    reply_to: int = None
    seen: bool = False
