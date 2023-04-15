
from pathlib import Path
from string import ascii_letters, digits

from fastapi import HTTPException
from pydantic import BaseSettings


class Settings(BaseSettings):
    home_dir: Path = Path(__file__).parent
    base_dir: Path = home_dir.parent

    users: dict[str, str]

    # user_pic_dir = base_dir / 'media/users/'

    token_expire = 7 * 24 * 3600
    token_abc = ascii_letters + digits + ('!@#$%^&*_+' * 2)


settings = Settings(_env_file='.env.secrets')


bad_auth = HTTPException(403, 'invalid user and pass')
