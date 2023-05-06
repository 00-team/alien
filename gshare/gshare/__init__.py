
import time

from .db import DbDict
from .logger import WeeklyRotating


def now() -> int:
    return int(time.time())


def format_duration(dur):
    if not dur:
        return ''

    return time.strftime('%H:%M:%S', time.gmtime(dur))


__all__ = [
    'DbDict',
    'WeeklyRotating',
    'now', 'format_duration'
]
