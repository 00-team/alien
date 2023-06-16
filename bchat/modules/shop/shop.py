
from deps import require_user_data
from models import UserModel
from settings import KW_USESCOR
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from utils import config

from .common import SHOP_IKB, SHOP_TEXT, Ctx


@require_user_data
async def shop(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    if user.id != config['ADMINS'][0]:
        return

    if update.callback_query:
        await update.callback_query.answer()
        await update.effective_message.edit_text(
            SHOP_TEXT,
            reply_markup=SHOP_IKB
        )
        return

    await update.message.reply_text(
        SHOP_TEXT,
        reply_markup=SHOP_IKB
    )


H_SHOP = [
    MessageHandler(
        filters.Text([KW_USESCOR]),
        shop, block=False
    ),
    CallbackQueryHandler(shop, pattern='show_shop')
]
