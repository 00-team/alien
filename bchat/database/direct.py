
import logging

from models import DirectModel, DirectTable
from settings import database
from sqlalchemy import select, update


async def get_direct(direct_id: int) -> DirectModel | None:
    query = select(DirectTable).where(
        DirectTable.direct_id == direct_id,
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
    query = select(DirectTable).where(
        DirectTable.user_id == user_id,
        DirectTable.seen == False
    ).limit(10)

    directs = []

    for result in await database.fetch_all(query):
        directs.append(DirectModel(**result))

    logging.info(f'not seen directs len: {len(directs)}/10')

    return directs


async def update_direct(direct_id: int, **values):
    return await database.execute(
        update(DirectTable)
        .where(
            DirectTable.direct_id == direct_id,
        )
        .values(**values)
    )
