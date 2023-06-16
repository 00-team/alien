

from deps import require_admin
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

    codes = ctx.args[1:]

    await update.effective_message.reply_text((
        f'amout: {amount} 🔥\ncodes: \n' +
        '\n'.join(codes)
    ))

H_CHARGE = [
    CommandHandler(['charge'], add_charge_codes),
]
