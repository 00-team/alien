
import logging

from models import Direct, DirectModel
from settings import database
from sqlalchemy import insert, select, update

# from sqlalchemy.orm import Query as Q


async def add_direct(user_id: int, sender_id: int, message_id: int, **kwds):
    query = insert(Direct).values(
        user_id=user_id,
        sender_id=sender_id,
        message_id=message_id,
        **kwds
    )
    return await database.execute(query)


async def get_direct(direct_id: int) -> DirectModel | None:
    query = select(Direct).where(
        Direct.direct_id == direct_id,
    )

    result = await database.fetch_one(query)
    if not result:
        return None

    return DirectModel(**result)


async def get_direct_notseen_count(user_id: int) -> int:
    query = (
        'SELECT COUNT(direct_id) FROM direct '
        'WHERE user_id = :user_id AND seen is false'
    )

    return (await database.fetch_one(query, {'user_id': user_id}))[0]


async def get_direct_notseen(user_id: int) -> list[DirectModel]:
    query = select(Direct).where(
        Direct.user_id == user_id,
        Direct.seen == False
    ).limit(10)

    directs = []

    for result in await database.fetch_all(query):
        directs.append(DirectModel(**result))

    logging.info(f'not seen directs len: {len(directs)}/10')

    return directs


async def update_direct(direct_id: int, **values):
    return await database.execute(
        update(Direct)
        .where(
            Direct.direct_id == direct_id,
        )
        .values(**values)
    )
