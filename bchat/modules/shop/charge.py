

from deps import require_user_data
from models import UserModel
from settings import KW_USESCOR
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from utils import config

from .common import CHARGE_IKB, CHARGE_RANGE, CHARGE_TEXT, SHOP_IKB, SHOP_TEXT
from .common import Ctx


@require_user_data
async def phone_charge(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    if user.id != config['ADMINS'][0]:
        return

    await update.callback_query.answer()
    await update.effective_message.edit_text(
        CHARGE_TEXT,
        reply_markup=CHARGE_IKB
    )


@require_user_data
async def buy_phone_charge(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    if not update.callback_query.data:
        return

    await update.effective_message.reply_text(update.callback_query.data)


H_CHARGE = [
    CallbackQueryHandler(
        phone_charge,
        pattern='^shop_phone_charge$',
        block=False
    ),
    CallbackQueryHandler(
        buy_phone_charge,
        pattern='^shop_buy_charge#[0-9]+$',
        block=False
    )
]
