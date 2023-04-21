
from time import time

from .db import *
from .logger import *
from .path import *


def now() -> int:
    return int(time())
