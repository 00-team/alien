
from db.shop import shop_add, shop_get
from db.user import user_update
from deps import require_user_data
from models import ItemType, ShopModel, ShopTable, UserModel, UserTable
from settings import KW_USESCOR
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from utils import config

from .common import CART_IKB, SHOP_IKB, SHOP_TEXT, Ctx


@require_user_data
async def shop(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    if user.id != config['ADMINS'][0]:
        return

    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text(
            SHOP_TEXT,
            reply_markup=SHOP_IKB
        )
        return

    await update.message.reply_text(
        SHOP_TEXT,
        reply_markup=SHOP_IKB
    )


@require_user_data
async def cart(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    items = await shop_get(
        ShopTable.user_id == user.id,
        ShopTable.done == False,
    )

    charge_text = ''
    member_text = ''

    for i in items:
        if i.item == ItemType.phone_charge:
            c = i.data['charge']
            charge_text = (
                f'🔋 کد شارژ {c} هزار تومانی - {i.score} امتیاز'
            )

        elif i.item == ItemType.channel_member:
            member_text = f'member - {i.score}'

    if not (charge_text or member_text):
        text = 'چیزی برای نمایش یافت نشد 😕'
    else:
        text += (
            'سبد خرید شما:\n\n' + charge_text + '\n\n' + member_text
        )

    await update.effective_message.edit_text(
        text,
        reply_markup=CART_IKB
    )


H_SHOP = [
    MessageHandler(
        filters.Text([KW_USESCOR]),
        shop, block=False
    ),
    CallbackQueryHandler(shop, pattern='^show_shop$'),
    CallbackQueryHandler(cart, pattern='^shop_cart$'),
]
