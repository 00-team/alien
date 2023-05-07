
import logging

from database import add_user, get_user
from telegram import Update
from telegram.ext import ContextTypes
from utils import toggle_code


async def user_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = await get_user(user.id)

    if user_data is None:
        code = toggle_code(int(await add_user(user.id, user.full_name)))
    else:
        code = toggle_code(user_data.row_id)

    logging.info(ctx.bot)
    logging.info(f'code: {code}')

    await update.message.reply_text(
        't.me/'
    )
