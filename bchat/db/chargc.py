

from models.shop import ChargcModel, ChargcTable
from settings import sqlx
from sqlalchemy import insert, select, update

Out = list[ChargcModel] | ChargcModel


async def chargc_get(*where, limit=10, offset=0) -> Out:
    query = select(ChargcTable).where(*where).offset(offset)

    if limit == 1:
        row = await sqlx.fetch_one(query)
        if not row:
            return None

        return ChargcModel(**row)

    rows = await sqlx.fetch_all(query.limit(limit))
    return [ChargcModel(**R) for R in rows]


async def chargc_update(*where, **values):
    await sqlx.execute(
        update(ChargcTable).where(*where),
        values
    )


async def chargc_add(**values) -> int:
    query = (
        select(ChargcTable)
        .where(ChargcTable.code == values['code'])
    )

    if await sqlx.fetch_one(query):
        return 0

    return await sqlx.execute(insert(ChargcTable), values)
