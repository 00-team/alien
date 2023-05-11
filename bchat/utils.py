
import base64
import logging
import sys

from settings import BYTE_ORDER

from gshare import DbDict

config = DbDict(sys.argv[1], load=True, indent=2)


def toggle_code(code: int | str) -> str | int | None:
    try:
        if isinstance(code, int):
            b = code.to_bytes(6, byteorder=BYTE_ORDER)
            return base64.b64encode(b).decode()
        else:
            b = base64.b64decode(code.encode())
            return int.from_bytes(b, byteorder=BYTE_ORDER)
    except Exception as e:
        logging.error('toggle code error:')
        logging.exception(e)

    return None
