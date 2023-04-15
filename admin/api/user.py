

from pydantic import BaseModel
from shared import bad_auth, settings

from .shared import router


class LoginBody(BaseModel):
    username: str
    password: str


@router.post('/login/')
async def login(body: LoginBody):
    upass = settings.users.get(body.username)
    if upass is None or upass != body.password:
        raise bad_auth

    return {'token': 'GG'}
