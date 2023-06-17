
from db.shop import shop_get
from deps import require_user_data
from models import ItemType, ShopTable, UserModel
from settings import KW_USESCOR
from telegram import Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters

from .common import CART_IKB, CHARGE_TEXT, MEMBER_TEXT, SHOP_IKB, Ctx


@require_user_data
async def shop(update: Update, ctx: Ctx, state: UserModel):
    ava_score = state.total_score - state.used_score

    text = (
        f'امتیاز شما: {ava_score} 🛍\n\n'
        f'{CHARGE_TEXT}\n\n{MEMBER_TEXT}\n.'
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text(
            text,
            reply_markup=SHOP_IKB
        )
        return

    await update.message.reply_text(
        text,
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
        if i.item_type == ItemType.charge:
            c = i.data['charge']
            charge_text = (
                f'🔋 کد شارژ {c} هزار تومانی - {i.score} امتیاز'
            )
            charge_text = i.reason

        elif i.item_type == ItemType.member:
            member_text = f'member - {i.score}'

    if not (charge_text or member_text):
        text = 'چیزی برای نمایش یافت نشد 😕'
    else:
        text = (
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
