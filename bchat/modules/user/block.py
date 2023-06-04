
import logging

from db.user import user_get, user_update
from deps import require_user_data
from models import UserModel, UserTable
from telegram import Update
from telegram.ext import CallbackQueryHandler

from .common import Ctx


@require_user_data
async def toggle_user_block(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()

    if update.effective_message:
        logging.info(update.message.reply_markup)
    else:
        logging.info('no message')

    uid = update.callback_query.data.split('#')[-1]
    target_user = await user_get(UserTable.user_id == int(uid))

    if not target_user:
        await update.effective_message.reply_text('کاربر پیدا نشد. ❌')
        await update.effective_message.edit_reply_markup()
        return

    if state.block_list.pop(uid, False):
        await update.effective_message.reply_text(
            'کاربر آزادسازی گردید. 🟢'
        )
    else:
        state.block_list[uid] = {
            'codename': target_user.codename,
            'name': target_user.name,
        }
        await update.effective_message.reply_text(
            'کاربر بلاک شد. 🔴'
        )

    await user_update(
        UserTable.user_id == state.user_id,
        block_list=state.block_list
    )


H_BLOCK = [
    CallbackQueryHandler(
        toggle_user_block,
        pattern='^toggle_user_block#[0-9]+$',
        block=False
    ),
]
