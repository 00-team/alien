
from .misc import H_MISC
from .sendall import H_SENDALL_CONV
from .shop import H_SHOP

HANDLERS_ADMIN = [
    *H_MISC,
    *H_SHOP,
    H_SENDALL_CONV
]
