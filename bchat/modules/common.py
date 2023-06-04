
from telegram.ext import ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


async def delete_message(ctx: Ctx, chat_id: int, message_id: int):
    try:
        await ctx.bot.delete_message(chat_id, message_id)
    except Exception:
        pass
