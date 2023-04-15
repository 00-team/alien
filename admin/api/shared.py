
from fastapi import APIRouter, Depends, Request

router = APIRouter(
    prefix='/api',
    tags=['api'],
)

_TOKENS = {
    'i007c': 'GG'
}


def set_token(user, token):
    pass


def require_token():
    def decorator(request: Request):
        print(request.headers)

    return Depends(decorator)
