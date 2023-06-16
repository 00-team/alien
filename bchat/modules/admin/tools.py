
import logging

from telegram import Update
from telegram.error import TimedOut
from telegram.ext import ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


async def send_user_info(update: Update, ctx: Ctx, user_id: int):
    try:
        chat = await ctx.bot.get_chat(user_id)

        await update.effective_message.reply_text(
            f'USERS INFO:\n'
            f'id: {chat.id}\n'
            f'name: {chat.full_name}\n'
            f'username: @{chat.username}\n',
        )
    except TimedOut:
        pass
    except Exception as e:
        logging.exception(e)
