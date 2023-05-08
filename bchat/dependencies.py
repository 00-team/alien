

import logging

from database import add_user, get_user
from models import UserModel
from telegram import Update
from telegram.ext import ContextTypes
from utils import config


def require_admin(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        if user.id in config['ADMINS']:
            return await func(update, ctx)

    return decorator


def require_user_data(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        user_data = await get_user(user.id)

        if user_data is None:
            row_id = await add_user(user.id, user.full_name)
            user_data = UserModel(
                row_id=row_id,
                user_id=user.id,
                name=user.full_name,
                gender=0
            )

        return await func(update, ctx, user_data)

    return decorator


'''
def require_joined(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.from_user:
            return

        not_joined = []
        user = update.message.from_user

        if user.is_bot:
            return

        user_add(user)

        if user.id in CONF['ADMINS']:
            await func(update, ctx)
            return

        for cid, cval in get_channels().items():
            cid = int(cid)
            if not cval['enable']:
                continue

            try:
                member = await ctx.bot.get_chat_member(cid, user.id)

                if member.status in ['left', 'kicked']:
                    chat = await ctx.bot.get_chat(cid)
                    if not chat.invite_link:
                        continue
                    not_joined.append([
                        InlineKeyboardButton(
                            chat.title, url=chat.invite_link
                        )
                    ])

            except NetworkError:
                continue
            except TelegramError as e:
                logging.exception(e)
                # channel_remove(chat_id)
                continue

        if not_joined:
            await update.message.reply_text(
                'اول مطمئن شوید که در کانال های زیر عضو شدید.',
                reply_markup=InlineKeyboardMarkup(not_joined)
            )

        else:
            await func(update, ctx)

    return decorator

'''

__all__ = [
    'require_admin',
    'require_user_data',
]
