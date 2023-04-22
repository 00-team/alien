

import random
import string
from urllib.parse import quote


class MediaError(Exception):
    pass


def escape(s: str) -> str:
    return quote(s, safe='~')


def random_string(lenght=30) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=lenght))
