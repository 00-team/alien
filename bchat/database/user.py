
from random import choices
from string import ascii_letters, digits

from models import UserTable
from settings import sqlx
from sqlalchemy import insert, select, update


def random_stirng(len=22):
    return ''.join(choices(ascii_letters + digits, k=len))


async def add_user(user_id: int, name: str):
    while True:
        random_code = random_stirng(23)
        if not (await sqlx.fetch_one(select(UserTable).where(
            UserTable.codename == random_code
        ))):
            break

    query = insert(UserTable).values(
        user_id=user_id,
        name=name,
        codename=random_code
    )
    await sqlx.execute(query)
    return random_code


async def update_user_code(user_id: int):
    query = 'SELECT user_id from users WHERE codename = :codename'

    while True:
        rc = random_stirng(23)
        if not (await sqlx.fetch_one(query, {'codename': rc})):
            codename = rc
            break

    await sqlx.execute(
        update(UserTable)
        .where(UserTable.user_id == user_id)
        .values(codename=codename)
    )

    return codename
