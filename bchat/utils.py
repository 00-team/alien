
from settings import BYTE_ORDER


def toggle_code(code: int | str) -> str | int:
    if isinstance(code, int):
        return code.to_bytes(4, byteorder=BYTE_ORDER).hex()

    return int.from_bytes(bytes.fromhex(code), byteorder=BYTE_ORDER)
