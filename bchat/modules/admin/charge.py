

from deps import require_admin
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


@require_admin
async def add_charge_codes(update: Update, ctx: Ctx):
    await update.effective_message.reply_text(' - '.join(ctx.args))

H_CHARGE = [
    CommandHandler(['charge'], add_charge_codes),
]
