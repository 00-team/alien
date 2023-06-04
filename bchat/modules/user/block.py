

import logging

from db.user import user_get, user_update
from deps import require_user_data
from models import UserModel, UserTable
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler

from .common import Ctx


@require_user_data
async def toggle_user_block(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    msg = update.effective_message
    keyboard = msg.reply_markup.inline_keyboard
    new_keyboard = []

    uid = update.callback_query.data.split('#')[-1]
    target_user = await user_get(UserTable.user_id == int(uid))
    text = 'آزاد سازی 🟢'

    if not target_user:
        await msg.reply_text(
            'کاربر پیدا نشد. ❌',
            reply_to_message_id=msg.id
        )
        await msg.edit_reply_markup()
        return

    if state.block_list.pop(uid, False):
        new_msg = await msg.reply_text(
            'کاربر آزادسازی گردید. 🟢',
            reply_to_message_id=msg.id
        )
        text = 'بلاک ⛔'

    else:
        state.block_list[uid] = {
            'codename': target_user.codename,
            'name': target_user.name,
        }
        new_msg = await msg.reply_text(
            'کاربر بلاک شد. 🔴',
            reply_to_message_id=msg.id
        )

    await user_update(
        UserTable.user_id == state.user_id,
        block_list=state.block_list
    )

    edit_msg = False

    for X in keyboard:
        row = []
        for Y in X:
            t, *_ = Y.callback_data.split('#')
            if t == 'toggle_user_block':
                if Y.text != text:
                    edit_msg = True

                row.append(InlineKeyboardButton(
                    callback_data=Y.callback_data,
                    text=text
                ))
            else:
                row.append(Y)

        new_keyboard.append(row)

    try:
        logging.info(
            f'block message diff: {new_msg.id - msg.id}'
        )
    except Exception as e:
        logging.exception(e)

    if edit_msg:
        await msg.edit_reply_markup(
            InlineKeyboardMarkup(new_keyboard)
        )


H_BLOCK = [
    CallbackQueryHandler(
        toggle_user_block,
        pattern='^toggle_user_block#[0-9]+$',
        block=False
    ),
]
