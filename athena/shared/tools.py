
import json
import time


def now():
    return int(time.time())


def get_config(path: str):
    with open(path, 'r') as f:
        return json.load(f)
