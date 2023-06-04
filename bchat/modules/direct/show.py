
import time

from db.direct import direct_get, direct_update
from db.user import user_update
from deps import require_user_data
from models import DirectModel, UserModel
from models.direct import DirectTable
from models.user import UserTable
from modules.admin import send_user_info
from modules.channels import require_joined
from modules.common import delete_message
from settings import KW_DRTNSEN
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext import filters
from utils import config

Ctx = ContextTypes.DEFAULT_TYPE


async def send_show_direct(
    update: Update, ctx: Ctx,
    direct: DirectModel, user_data: UserModel
):
    chat_id = update.effective_message.chat_id

    if not direct:
        return

    repdir_mid = None
    msg_id = None

    if direct.reply_to:
        repdir = await direct_get(
            DirectTable.direct_id == direct.reply_to,
            limit=1
        )
        if repdir:
            repdir_mid = repdir.message_id

    await direct_update(
        DirectTable.direct_id == direct.direct_id,
        seen=True
    )

    try:
        msg_id = await ctx.bot.copy_message(
            chat_id, direct.sender_id, direct.message_id,
            reply_to_message_id=repdir_mid,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    'پاسخ ✍', callback_data=f'direct_reply#{direct.direct_id}'
                ),
                InlineKeyboardButton(
                    'بلاک ⛔',
                    callback_data=f'toggle_user_block#{direct.sender_id}'
                ),
            ]])
        )
    except Exception:
        pass

    if direct.from_admin:
        return

    if chat_id in config['ADMINS']:
        await send_user_info(update, ctx, direct.sender_id)

    if msg_id and not direct.seen:
        try:
            await ctx.bot.send_message(
                direct.sender_id, 'پیام شما مشاهده شد. 🧉',
                reply_to_message_id=direct.message_id
            )
        except Exception:
            pass

    if not msg_id:
        return

    if user_data.direct_msg_id:
        await delete_message(ctx, chat_id, user_data.direct_msg_id)
        await user_update(
            UserTable.user_id == user_data.user_id,
            direct_msg_id=None
        )


@require_joined
@require_user_data
async def show_directs(update: Update, ctx: Ctx, user_data: UserModel):
    direct_id = 'all'
    user_id = update.effective_user.id
    is_admin = user_id in config['ADMINS']

    if update.callback_query:
        await update.callback_query.answer()
        direct_id = update.callback_query.data.split('#')[-1]

    if direct_id == 'all':
        directs = await direct_get(
            DirectTable.user_id == user_id,
            DirectTable.seen == False,
            limit=20 if is_admin else 10
        )
    else:
        directs = await direct_get(
            DirectTable.direct_id == int(direct_id)
        )

    if not directs:
        await update.effective_message.reply_text(
            'پیامی یافت نشد! 🧊'
        )
        return

    if len(directs) == 1:
        await send_show_direct(update, ctx, directs[0], user_data)
        return

    for direct in directs:
        await send_show_direct(update, ctx, direct, user_data)
        time.sleep(1)


H_DIRECT_SHOW = [
    CallbackQueryHandler(
        show_directs,
        pattern='^show_direct#(all|[0-9]+)$',
        block=False
    ),
    MessageHandler(
        filters.Text([KW_DRTNSEN]),
        show_directs,
        block=False,
    )
]
