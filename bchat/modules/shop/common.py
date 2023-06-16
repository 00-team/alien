
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

CHARGE_RANGE = (
    # score - charge in toman
    (100, '20'),
    (200, '40'),
    (400, '50')
)

MEMBER_RANGE = (
    # score - member
    (100, 50),
    (200, 100),
    (500, 150),
)


CHARGE_TEXT = (
    '\n\nتعرفه کد شارژ 🔋\n\n'
    '\n'.join([
        f'{r[0]} امتیاز - کد شارژ {r[1]} هزار تومانی' for r in CHARGE_RANGE
    ])
)


MEMBER_TEXT = (
    '\n\nتعرفه ممبر 😺\n\n'
    '\n'.join([
        f'{r[0]} امتیاز - {r[1]} ممبر' for r in CHARGE_RANGE
    ])
)
