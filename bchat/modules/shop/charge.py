

from db.shop import shop_add, shop_get
from db.user import user_update
from deps import require_user_data
from models import ItemType, ShopTable, UserModel, UserTable
from telegram import Update
from telegram.ext import CallbackQueryHandler

from .common import CHARGE_PTC, CHARGE_PTC_IKB, CHARGE_RANGE, CHARGE_TEXT
from .common import GET_SCORE_IKB, SHOP_CART_IKB, Ctx, get_charge_ikb


@require_user_data
async def phone_charge(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    await update.effective_message.edit_text(
        'اپراتور خود را انتخاب کنید 🌊',
        reply_markup=CHARGE_PTC_IKB
    )


@require_user_data
async def charge_amount(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    data = update.callback_query.data
    if not data:
        return

    _, ptc = data.split('#')

    ptc_display = CHARGE_PTC[ptc]

    text = (
        f'اپراتور انتخابی شما: {ptc_display}\n\n{CHARGE_TEXT}\n.'
    )

    await update.effective_message.edit_text(
        text,
        reply_markup=get_charge_ikb(ptc)
    )


@require_user_data
async def buy_phone_charge(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    data = update.callback_query.data
    user = update.effective_user

    if not data:
        return

    a, ptc, idx = data.split('#')
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
        ShopTable.item_type == ItemType.charge,
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
        reason=f'شارژ {charge} هزار تومانی ' + CHARGE_PTC[ptc],
        item_type=ItemType.charge,
        data={'charge': charge, 'ptc': ptc}
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
        charge_amount,
        pattern='^shop_charge_ptc#(irmci|irancell|rightel)$',
        block=False
    ),
    CallbackQueryHandler(
        buy_phone_charge,
        pattern='^shop_buy_charge#(irmci|irancell|rightel)#[0-9]+$',
        block=False
    )
]
