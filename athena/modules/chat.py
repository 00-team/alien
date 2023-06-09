
from shared.database import channel_add, channel_add_member, channel_remove
from shared.database import get_users
from telegram import Update
from telegram.ext import ContextTypes


async def chat_member_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    chat_member = update.chat_member.new_chat_member
    user_id = str(chat_member.user.id)

    if chat_member.status == 'member' and user_id in get_users():
        channel_add_member(chat.id)


async def my_chat_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    e = update.my_chat_member
    status = e.new_chat_member.status
    user_id = e.from_user.id
    name = e.chat.title

    if e.chat.type not in ['channel', 'supergroup']:
        # await ctx.bot.leave_chat(e.chat.id)
        return

    if status == 'administrator':
        channel_add(e.chat.id)

        await ctx.bot.send_message(
            user_id,
            f'channel {name} was added ✅'
        )
    else:
        channel_remove(e.chat.id)
        if status not in ['left', 'kicked']:
            await ctx.bot.leave_chat(e.chat.id)
