from pathlib import Path

HOME_DIR = Path(__file__).parent.parent
BASE_DIR = HOME_DIR.parent


__all__ = [
    'HOME_DIR',
    'BASE_DIR'
]
