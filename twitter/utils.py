import json
import logging
import sys
from logging import FileHandler, Formatter, StreamHandler
from pathlib import Path
from random import choices

BASE_DIR = Path(__file__).parent
SECRETS_DIR = BASE_DIR / 'secrets'
DATA_DIR = BASE_DIR / 'data'

with open(sys.argv[1], 'r') as f:
    CONF = json.load(f)

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

    term = StreamHandler()
    term.setFormatter(formatter)

    logger = logging.getLogger('bot')
    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler)
    logger.addHandler(term)

    return logger


def last_retweet(name: str, hashtag: str, tweet_id: str = None):
    hashtag_path = DATA_DIR / f'{name}_{hashtag}_LR'
    path = DATA_DIR / f'{name}_LR'

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


def read_shared_db(name: str):
    with open(DATA_DIR / f'{name}.shared.json', 'r') as f:
        return json.load(f)


EMOJI_SET = [
    '💥', '💸', '💵', '💴', '💶', '💷', '🪙', '💰', '💎',
    '🎨', '🔥', '❤', '🧡', '💛', '💚', '💙', '💜', '🤍', '💗'
]


def format_with_emojis(text: str) -> str:
    return text.format(*choices(EMOJI_SET, k=10))
