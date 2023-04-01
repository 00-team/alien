
import json

from .settings import DB_PATH

_DB = {
    'search': 'drop nft',
    'active': False,
    'reply_tweets': [],
}


def read_db():
    with open(DB_PATH, 'r') as f:
        return json.load(f)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_json(data, path):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def save_db():
    with open(DB_PATH, 'w') as f:
        json.dump(_DB, f)


def setup_db(db, path):
    if not path.exists():
        save_json(db, path)
        return db

    with open(path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError('invalid database')

    return {**db, **data}


def setup_databases():
    global _DB

    _DB = setup_db(_DB, DB_PATH)


def update_search(value: str = None) -> str | None:
    if value:
        _DB['search'] = value
        save_db()

    return _DB['search']


def add_reply(value: str):
    _DB['reply_tweets'].append(value)
    save_db()


def del_reply(idx: int):
    if idx >= len(_DB['reply_tweets']):
        return

    del _DB['reply_tweets'][idx]
    save_db()


def get_replys() -> list[str]:
    return _DB['reply_tweets']


def update_active(toggle: bool = False) -> bool:
    if toggle:
        _DB['active'] = not _DB['active']
        save_db()

    return _DB['active']
