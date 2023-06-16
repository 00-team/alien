

from db.shop import shop_add, shop_get
from db.user import user_update
from deps import require_user_data
from models import ItemType, ShopTable, UserModel, UserTable
from telegram import Update
from telegram.ext import CallbackQueryHandler
from utils import config

from .common import CHARGE_IKB, CHARGE_RANGE, CHARGE_TEXT, GET_SCORE_IKB
from .common import SHOP_CART_IKB, Ctx


@require_user_data
async def phone_charge(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    if user.id != config['ADMINS'][0]:
        return

    await update.callback_query.answer()
    await update.effective_message.edit_text(
        CHARGE_TEXT,
        reply_markup=CHARGE_IKB
    )


@require_user_data
async def buy_phone_charge(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    data = update.callback_query.data
    user = update.effective_user

    if not data:
        return

    a, idx = data.split('#')
    if a != 'shop_buy_charge':
        return

    idx = int(idx)
    idx = max(min(len(CHARGE_RANGE)-1, idx), 0)

    price, charge = CHARGE_RANGE[idx]
    ava_score = state.total_score - state.used_score

    if ava_score < price:
        await update.effective_message.edit_text(
            'امتیاز شما برای این خرید کافی نیست ❌',
            reply_markup=GET_SCORE_IKB
        )
        return

    item = await shop_get(
        ShopTable.user_id == user.id,
        ShopTable.done == False,
        ShopTable.item == ItemType.phone_charge,
        limit=1
    )
    if item:
        await update.effective_message.edit_text(
            'شما یک درخواست فعال دارید. ❌\n' + item.reason,
            reply_markup=SHOP_CART_IKB
        )
        return

    await shop_add(
        user_id=user.id,
        score=price,
        reason=f'شارژ {charge} هزار تومانی',
        item=ItemType.phone_charge,
        data={'charge': charge}
    )
    await user_update(
        UserTable.user_id == user.id,
        used_score=state.used_score + price
    )

    await update.effective_message.edit_text(
        'شارژ برای شما ارسال خواهد شد. ✅',
        reply_markup=SHOP_CART_IKB
    )


H_CHARGE = [
    CallbackQueryHandler(
        phone_charge,
        pattern='^shop_phone_charge$',
        block=False
    ),
    CallbackQueryHandler(
        buy_phone_charge,
        pattern='^shop_buy_charge#[0-9]+$',
        block=False
    )
]
