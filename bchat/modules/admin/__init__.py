
from .dev import H_DEV
from .misc import H_MISC
from .sendall import H_SENDALL_CONV
from .shop import H_SHOP
from .usernames import H_GETUN

HANDLERS_ADMIN = [
    *H_MISC,
    *H_SHOP,
    *H_DEV,
    *H_GETUN,
    H_SENDALL_CONV,
]
