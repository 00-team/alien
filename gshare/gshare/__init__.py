
import time

from .db import DbDict
from .logger import WeeklyRotating, setup_logging
from .tel import get_error_handler


def now() -> int:
    return int(time.time())


def format_duration(dur):
    if not dur:
        return ''

    return time.strftime('%H:%M:%S', time.gmtime(dur))


__all__ = [
    'DbDict',
    'WeeklyRotating', 'setup_logging',
    'now', 'format_duration', 'get_error_handler'
]
