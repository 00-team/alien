
from models import UserModel, Users
from settings import database
from sqlalchemy import insert, select, update


async def add_user(user_id: int, name: str):
    query = insert(Users).values(
        user_id=user_id,
        name=name,
    )
    return await database.execute(query)


async def get_user(user_id: int = None, code: int = None) -> None | UserModel:
    if not (user_id or code):
        return None

    if user_id:
        query = select(Users).where(Users.user_id == user_id)
    else:
        query = select(Users).where(Users.code == code)

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
