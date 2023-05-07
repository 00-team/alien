
import logging

from database import add_user, get_user
from settings import config
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

    bot_username = config['BOT_USERNAME']

    logging.info(ctx.bot)
    logging.info(f'code: {code}')

    await update.message.reply_text(
        f't.me/{bot_username}'
    )
