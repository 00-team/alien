

from deps import require_user_data
from models import UserModel
from settings import KW_USESCOR
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from utils import config

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def phone_charge(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    if user.id != config['ADMINS'][0]:
        return

    await update.message.reply_text(
        'shop',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'charge',
                callback_data='shop_phone_charge'
            ),
            InlineKeyboardButton(
                'member',
                callback_data='shop_channel_member'
            )
        ]])
    )


H_CHARGE = [
    CallbackQueryHandler(
        phone_charge,
        pattern='^shop_phone_charge$',
        block=False
    )
]
