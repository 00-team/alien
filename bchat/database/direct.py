
from models import Direct, DirectModel
from settings import database
from sqlalchemy import insert, select, update

# from sqlalchemy.orm import Query as Q


async def add_direct(user_id: int, sender_id: int, message_id: int):
    query = insert(Direct).values(
        user_id=user_id,
        sender_id=sender_id,
        message_id=message_id,
    )
    return await database.execute(query)


async def get_direct(direct_id: int, user_id: int) -> DirectModel | None:
    query = select(Direct).where(
        Direct.user_id == user_id,
        Direct.direct_id == direct_id,
    )

    result = await database.fetch_one(query)
    if not result:
        return None

    return DirectModel(**result)


async def get_direct_notseen_count(user_id: int) -> int:
    # query = Q(Direct).filter(
    #     Direct.user_id == user_id,
    #     Direct.seen is False
    # ).count()

    query = (
        'SELECT COUNT(direct_id) FROM direct '
        'WHERE user_id = :user_id AND seen is false'
    )

    return await database.fetch_one(query, {'user_id': user_id})


async def get_direct_notseen(user_id: int) -> list[DirectModel]:
    query = select(Direct).where(
        Direct.user_id == user_id,
        Direct.seen is False
    ).limit(10)

    for result in await database.fetch_all(query):
        yield DirectModel(**result)


async def update_direct(direct_id: int, user_id: int, seen=True):
    return await database.execute(
        update(Direct)
        .where(
            Direct.user_id == user_id,
            Direct.direct_id == direct_id,
        )
        .values(seen=seen)
    )
