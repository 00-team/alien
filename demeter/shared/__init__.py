
import time

from .db import *
from .logger import *
from .path import *


def now() -> int:
    return int(time.time())


def format_duration(dur):
    if not dur:
        return ''

    return time.strftime('%H:%M:%S', time.gmtime(dur))
