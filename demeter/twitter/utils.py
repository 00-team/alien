

import random
import string
from urllib.parse import quote


class MediaError(Exception):
    pass


def escape(s: str) -> str:
    return quote(s, safe='~')

    # s = quote(s.encode('utf-8'), safe=b'~')
    #
    # if isinstance(s, bytes):
    #     s = s.decode('utf-8')
    #
    # return s


def random_string(lenght=30) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=lenght))
