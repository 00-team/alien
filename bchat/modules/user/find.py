

import logging

from deps import require_user_data
from models.user import UserModel
from settings import KW_CTSPLCN
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ConversationHandler
from telegram.ext import MessageHandler, filters
from utils import config

from .common import Ctx


@require_user_data
async def find_user_start(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user

    if user.id != config['ADMINS'][0]:
        return ConversationHandler.END

    await update.effective_message.reply_text(
        'send a username or forward a message from the user',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'لغو ❌', callback_data='cancel_find_user'
            )
        ]])
    )


@require_user_data
async def find_user(update: Update, ctx: Ctx, state: UserModel):
    logging.info(update.to_dict())
    # return ConversationHandler.END


@require_user_data
async def cancel(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    try:
        await update.effective_message.delete()
    except Exception:
        pass

    return ConversationHandler.END


H_FIND_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        MessageHandler(
            filters.Text([KW_CTSPLCN]),
            find_user_start, block=False
        )
    ],
    states={
        'FIND_USER': [
            MessageHandler(
                filters.ChatType.PRIVATE,
                find_user,
            )
        ],
    },
    fallbacks=[CallbackQueryHandler(
        cancel,
        pattern='^cancel_find_user$'
    )])
