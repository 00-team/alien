from models.direct import DirectModel, DirectTable
from settings import sqlx
from sqlalchemy import insert, select, update


async def direct_get(*where, limit=10) -> list[DirectModel]:
    rows = await sqlx.fetch_all(
        select(DirectTable).where(*where).limit(limit)
    )

    return [DirectModel(**R) for R in rows]


async def direct_update(*where, **values):
    await sqlx.execute(
        update(DirectTable).where(*where),
        values
    )


async def direct_add(**values) -> int:
    return await sqlx.execute(insert(DirectTable), values)
