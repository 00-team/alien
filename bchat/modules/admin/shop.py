

import logging
import time

from db.chargc import chargc_add, chargc_get
from db.shop import shop_get, shop_update
from deps import require_admin
from models import ChargcTable, ItemType, ShopTable
from modules.shop.common import CHARGE_PTC, CHARGE_RANGE
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


@require_admin
async def add_charge_codes(update: Update, ctx: Ctx):
    msg = update.effective_message
    usage = (
        f'/charge <{" - ".join(CHARGE_PTC.keys())}> 20\n'
        'code1\ncode2\n...'
    )
    if len(ctx.args) < 3:
        await msg.reply_text(usage)
        return

    try:
        amount = int(ctx.args[1])
        ptc = ctx.args[0]
        if ptc not in CHARGE_PTC.keys():
            raise ValueError

        for _, a in CHARGE_RANGE:
            if amount == a:
                break
        else:
            await msg.reply_text(
                f'invalid amount {amount}'
            )
            raise ValueError
    except Exception:
        await msg.reply_text(usage)
        return

    items = await shop_get(
        ShopTable.item_type == ItemType.charge,
        ShopTable.done == False,
    )

    codes = ctx.args[2:]

    for i in items:
        if amount == i.data['charge'] and ptc == i.data['ptc']:
            try:
                await ctx.bot.send_message(
                    i.user_id,
                    f'کد شارژ {CHARGE_PTC[ptc]} شما:\n{codes.pop()}'
                )
                await shop_update(
                    ShopTable.item_id == i.item_id,
                    done=True
                )
                await msg.reply_text('sent a code to a user ✅')
                time.sleep(1)
            except Exception as e:
                logging.exception(e)

    added = 0
    for code in codes:
        if await chargc_add(amount=amount, code=code, op=ptc):
            added += 1

    await msg.reply_text(
        f'added {added} codes'
    )


@require_admin
async def show_shop(update: Update, ctx: Ctx):
    offset = 0
    try:
        offset = int(ctx.args[0]) * 10
    except Exception:
        pass

    items = await shop_get(ShopTable.done == False, offset=offset)
    text = 'shop items:\n'

    for i in items:
        text += f'[{i.item_id}] {i.reason}\n'

    await update.effective_message.reply_text(text)


@require_admin
async def show_codes(update: Update, ctx: Ctx):
    offset = 0
    try:
        offset = int(ctx.args[0]) * 10
    except Exception:
        pass

    items = await chargc_get(ChargcTable.used == False, offset=offset)
    text = 'unused codes:\n'

    for i in items:
        text += f'[{i.cc_id}] {i.op} {i.amount} {i.code}\n'

    await update.effective_message.reply_text(text)


H_SHOP = [
    CommandHandler(['charge'], add_charge_codes),
    CommandHandler(['shop'], show_shop),
    CommandHandler(['charge_codes'], show_codes),
]
