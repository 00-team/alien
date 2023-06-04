from models.direct import DirectModel, DirectTable
from settings import sqlx
from sqlalchemy import insert, select, update


async def direct_get(*where, limit=10) -> list[DirectModel] | DirectModel:
    query = select(DirectTable).where(*where)

    if limit == 1:
        row = await sqlx.fetch_one(query)
        if not row:
            return None

        return DirectModel(**row)

    rows = await sqlx.fetch_all(query.limit(limit))
    return [DirectModel(**R) for R in rows]


async def direct_update(*where, **values):
    await sqlx.execute(
        update(DirectTable).where(*where),
        values
    )


async def direct_add(**values) -> int:
    return await sqlx.execute(insert(DirectTable), values)


async def direct_unseen_count(user_id: int) -> int:
    query = (
        'SELECT COUNT(direct_id) FROM direct '
        'WHERE user_id = :user_id AND seen is false'
    )

    return (await sqlx.fetch_one(query, {'user_id': user_id}))[0]
