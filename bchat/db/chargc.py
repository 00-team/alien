

from models.shop import ChargcModel, ChargcTable
from settings import sqlx
from sqlalchemy import insert, select, update


async def chargc_get(*where) -> ChargcModel:
    query = select(ChargcTable).where(*where)

    row = await sqlx.fetch_one(query)
    if not row:
        return None

    return ChargcModel(**row)


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
