
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE

CHARGE_RANGE = (
    # score - charge in toman
    (100, '20'),
    (200, '40'),
    (400, '50'),
    (800, '810'),
    (1200, '250'),
)

MEMBER_RANGE = (
    # score - member
    (100, 50),
    (200, 100),
    (500, 150),
)


CHARGE_TEXT = (
    '\n\nتعرفه کد شارژ 🔋\n\n' + '\n'.join([
        f'{r[0]} امتیاز - کد شارژ {r[1]} هزار تومانی' for r in CHARGE_RANGE
    ])
)


MEMBER_TEXT = (
    '\n\nتعرفه ممبر 😺\n\n' + '\n'.join([
        f'{r[0]} امتیاز - {r[1]} ممبر' for r in CHARGE_RANGE
    ])
)

SHOP_TEXT = CHARGE_TEXT + MEMBER_TEXT
SHOP_IKB = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        'charge',
        callback_data='shop_phone_charge'
    ),
    InlineKeyboardButton(
        'member',
        callback_data='shop_channel_member'
    )
]])

SHOP_BTN = InlineKeyboardButton(
    'show shop 🏪',
    callback_data='show_shop'
)

keyboard = [[]]

for i, r in enumerate(CHARGE_RANGE):
    if i % 2:
        keyboard.append([])

    keyboard[-1].append(InlineKeyboardButton(
        f'{r[0]} ⚡',
        callback_data=f'shop_buy_charge#{i}'
    ))

CHARGE_IKB = InlineKeyboardMarkup([
    *keyboard,
    [SHOP_BTN]
])


keyboard = [[]]

for i, r in enumerate(MEMBER_RANGE):
    if i % 2:
        keyboard.append([])

    keyboard[-1].append(InlineKeyboardButton(
        f'{r[0]} 🤡',
        callback_data=f'shop_buy_member#{i}'
    ))

MEMBER_IKB = InlineKeyboardMarkup([
    *keyboard,
    [SHOP_BTN]
])
