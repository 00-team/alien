
from random import choices
from string import ascii_letters, digits

from models import UserModel, Users
from settings import database
from sqlalchemy import insert, select, update


def random_stirng(len=22):
    return ''.join(choices(ascii_letters + digits, k=len))


async def add_user(user_id: int, name: str):
    while True:
        random_code = random_stirng(23)
        if not (await database.fetch_one(select(Users).where(
            Users.codename == random_code
        ))):
            break

    query = insert(Users).values(
        user_id=user_id,
        name=name,
        codename=random_code
    )
    return await database.execute(query), random_code


async def get_user(user_id=None, codename=None) -> None | UserModel:
    if not (user_id is None or codename is None):
        return None

    if user_id:
        query = select(Users).where(Users.user_id == user_id)
    else:
        query = select(Users).where(Users.codename == codename)

    result = await database.fetch_one(query)
    if not result:
        return None

    return UserModel(**result)


async def update_user(user_id: int, **values):
    if not values:
        return

    return await database.execute(
        update(Users)
        .where(Users.user_id == user_id)
        .values(**values)
    )


async def update_user_code(user_id: int, codename=None):
    query = 'SELECT user_id from users WHERE codename = :codename'

    if codename:
        if await database.fetch_one(query, {'codename': codename}):
            raise ValueError('codename exists')
    else:
        while True:
            rc = random_stirng(23)
            if not (await database.fetch_one(query, {'codename': rc})):
                codename = rc
                break

    return await database.execute(
        update(Users)
        .where(Users.user_id == user_id)
        .values(codename=codename)
    ), codename
