
import base64

from settings import BYTE_ORDER


def toggle_code(code: int | str) -> str | int:
    if isinstance(code, int):
        b = code.to_bytes(6, byteorder=BYTE_ORDER).hex()
        return base64.b64encode(b).decode()
    else:
        b = base64.b64decode(code.encode())
        return int.from_bytes(b, byteorder=BYTE_ORDER)
