import json
import logging
from logging import FileHandler, Formatter
from pathlib import Path

BASE_DIR = Path(__file__).parent
SECRETS_DIR = BASE_DIR / 'secrets'
DATA_DIR = BASE_DIR / 'data'

SECRETS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def get_logger(name: str):
    formatter = Formatter(
        fmt='%(asctime)s.%(msecs)03d <%(levelname)s>: %(message)s',
        datefmt='%H:%M:%S'
    )

    handler = FileHandler(BASE_DIR / f'{name}.log', encoding='utf-8')
    handler.setFormatter(formatter)

    logger = logging.getLogger('bot')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger


def last_retweet(name: str, hashtag: str, tweet_id: str | None = None):
    hashtag_path = DATA_DIR / f'{name}_{hashtag}_last_retweet'
    path = DATA_DIR / f'{name}_last_retweet'

    if tweet_id:
        with open(path, 'w') as f:
            f.write(tweet_id)

        with open(hashtag_path, 'w') as f:
            f.write(tweet_id)
    else:
        last_rt, last_hashtag_rt = None, None

        if path.is_file():
            with open(path) as f:
                last_rt = f.read()

        if hashtag_path.is_file():
            with open(hashtag_path) as f:
                last_hashtag_rt = f.read()

        return last_rt, last_hashtag_rt


def get_config(path: str):
    with open(path, 'r') as f:
        return json.load(f)
