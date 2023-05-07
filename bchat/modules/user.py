
from database import get_user
from telegram import Update
from telegram.ext import ContextTypes
from utils import toggle_code


async def user_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_data = get_user(user.id)

    await update.message.reply_text(
        ''
    )
