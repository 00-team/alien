
import time
from random import choices

EMOJI_SET = [
    '💥', '💸', '💵', '💴', '💶', '💷', '🪙', '💰', '💎',
    '🎨', '🔥', '❤', '🧡', '💛', '💚', '💙', '💜', '🤍', '💗'
]


def now():
    return int(time.time())


def format_with_emojis(text: str) -> str:
    return text.format(*choices(EMOJI_SET, k=10))
