

from models.shop import ShopModel, ShopTable
from settings import sqlx
from sqlalchemy import insert, select, update


async def shop_get(*where, limit=10) -> list[ShopModel] | ShopModel:
    query = select(ShopTable).where(*where)

    if limit == 1:
        row = await sqlx.fetch_one(query)
        if not row:
            return None

        return ShopModel(**row)

    rows = await sqlx.fetch_all(query.limit(limit))
    return [ShopModel(**R) for R in rows]


async def shop_update(*where, **values):
    await sqlx.execute(
        update(ShopTable).where(*where),
        values
    )


async def shop_add(**values) -> int:
    return await sqlx.execute(insert(ShopTable), values)


async def shop_undone_count(user_id: int) -> int:
    query = (
        'SELECT COUNT(user_id) FROM shop '
        'WHERE done is false'
    )

    return (await sqlx.fetch_one(query))[0]
