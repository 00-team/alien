
import base64
import sys

from settings import BYTE_ORDER

from gshare import DbDict

config = DbDict(sys.argv[1], load=True)


def toggle_code(code: int | str) -> str | int:
    if isinstance(code, int):
        b = code.to_bytes(6, byteorder=BYTE_ORDER)
        return base64.b64encode(b).decode()
    else:
        b = base64.b64decode(code.encode())
        return int.from_bytes(b, byteorder=BYTE_ORDER)
