import json
import logging
import random
import string
import time
from pathlib import Path

import httpx
from flask import render_template

BASE_DIR = Path(__file__).parent
BOT_INFO_URL = 'https://api.twitter.com/2/users/me'


def error(message: str):
    error = {
        'message': message
    }

    return render_template('index.html', error=error), 400


def merge_params(url: str, params: dict) -> str:
    params_str = '&'.join(map(lambda i: f'{i[0]}={i[1]}', params.items()))
    return url + '?' + params_str


def random_string(lenght=30) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=lenght))


def get_bot_info(token: str) -> dict:
    headers = {'Authorization': f'Bearer {token}'}
    response = httpx.get(BOT_INFO_URL, headers=headers)

    return response.json().get('data', {})


def save_bot_token(data: dict):
    if not isinstance(data, dict) or data.get('access_token') is None:
        raise ValueError('Error to Save Bot Token')

    access_token = data['access_token']
    refresh_token = data['refresh_token']
    expires_in = data['expires_in']

    bot = {
        **get_bot_info(access_token),
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': int(time.time() + expires_in),
    }

    filename = bot['username']

    with open(BASE_DIR / f'{filename}.json', 'w') as f:
        json.dump(bot, f, indent=4)


def get_logger(name: str):
    formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d <%(levelname)s>: %(message)s',
        datefmt='%H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger
