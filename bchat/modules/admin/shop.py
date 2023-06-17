

import logging

from db.chargc import chargc_add
from db.shop import shop_get, shop_update
from deps import require_admin
from models import ItemType, ShopTable
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


@require_admin
async def add_charge_codes(update: Update, ctx: Ctx):
    if len(ctx.args) < 2:
        await update.effective_message.reply_text('/charge 20\ncode1\ncode2')
        return

    try:
        amount = int(ctx.args[0])
    except Exception:
        await update.effective_message.reply_text('/charge 20\ncode1\ncode2')
        return

    items = await shop_get(
        ShopTable.item_type == ItemType.charge,
        ShopTable.done == False,
    )

    codes = ctx.args[1:]

    for i in items:
        if amount == i.data['charge']:
            try:
                await ctx.bot.send_message(
                    i.user_id,
                    f'شارژ شما: {codes.pop()}'
                )
                await shop_update(
                    ShopTable.item_id == i.item_id,
                    done=True
                )
            except Exception as e:
                logging.exception(e)

    for code in ctx.args[1:]:
        await chargc_add(amount=amount, code=code)


@require_admin
async def show_shop(update: Update, ctx: Ctx):
    offset = 0
    try:
        offset = int(ctx.args[0]) * 10
    except Exception:
        pass

    items = await shop_get(ShopTable.done == False, offset=offset)
    text = ''

    for i in items:
        text += f'[{i.item_id}] {i.reason}\n'

    await update.effective_message.reply_text(text)

H_SHOP = [
    CommandHandler(['charge'], add_charge_codes),
    CommandHandler(['shop'], show_shop)
]
