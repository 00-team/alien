
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE

CHARGE_RANGE = (
    # score - charge in toman
    (100, 20),
    (200, 45),
    (300, 70),
    (400, 100),
    (500, 120),
    (1000, 250),
)
CHARGE_PTC = {
    'irancell': 'ایرانسل 🟡',
    'irmci': 'همراه اول 🔵',
    'rightel': 'رایتل 🟣',
}

MEMBER_RANGE = (
    # score - member
    (500, 300),
    (1000, 650),
)


CHARGE_TEXT = (
    'تعرفه کد شارژ 🔋\n\n' + '\n'.join([
        f'{r[0]} امتیاز - کد شارژ {r[1]} هزار تومانی' for r in CHARGE_RANGE
    ])
)
MEMBER_TEXT = (
    'تعرفه ممبر 😺\n\n' + '\n'.join([
        f'{r[0]} امتیاز - {r[1]} ممبر' for r in MEMBER_RANGE
    ])
)


CART_BTN = InlineKeyboardButton(
    'سبد خرید 📦',
    callback_data='shop_cart'
)
SHOP_BTN = InlineKeyboardButton(
    'فروشگاه 🏪',
    callback_data='show_shop'
)

CS_COM_BTNS = [
    InlineKeyboardButton(
        'شارژ 🔋',
        callback_data='shop_phone_charge'
    ),
    InlineKeyboardButton(
        'ممبر 😺',
        # callback_data='shop_channel_member'
        callback_data='coming_soon'
    ),

]

SHOP_IKB = InlineKeyboardMarkup([
    CS_COM_BTNS,
    [CART_BTN],
])
CART_IKB = InlineKeyboardMarkup([
    CS_COM_BTNS,
    [SHOP_BTN],
])
SHOP_CART_IKB = InlineKeyboardMarkup([[SHOP_BTN, CART_BTN]])


GET_SCORE_IKB = InlineKeyboardMarkup([
    [InlineKeyboardButton(
        'جمع آوری امتیاز 🌟',
        callback_data='user_link'
    )],
    [SHOP_BTN, CART_BTN],
])


CHARGE_PTC_IKB = InlineKeyboardMarkup([
    [InlineKeyboardButton(
        p[1], callback_data=f'shop_charge_ptc#{p[0]}'
    ) for p in CHARGE_PTC.items()],
    [SHOP_BTN, CART_BTN]
])


def get_charge_ikb(ptc: str):
    keyboard = [[]]

    for i, r in enumerate(CHARGE_RANGE):
        if i % 2:
            keyboard.append([])

        keyboard[-1].append(InlineKeyboardButton(
            f'{r[0]} ⚡',
            callback_data=f'shop_buy_charge#{ptc}#{i}'
        ))

    return InlineKeyboardMarkup([
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
