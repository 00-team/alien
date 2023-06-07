from models.user import UserModel, UserTable
from settings import sqlx
from sqlalchemy import insert, select, update


async def user_get(*where) -> UserModel | None:
    row = await sqlx.fetch_one(
        select(UserTable).where(*where)
    )
    if not row:
        return None

    return UserModel(**row)


async def user_update(*where, **values):
    await sqlx.execute(
        update(UserTable).where(*where),
        values
    )


async def user_add(**values) -> int:
    return await sqlx.execute(insert(UserTable), values)


async def user_count(not_blocked=True) -> int:
    query = 'SELECT COUNT(user_id) FROM users'
    if not_blocked:
        query += ' WHERE blocked_bot is false'

    return (await sqlx.fetch_one(query))[0]
