

from db.user import user_get, user_update
from deps import require_user_data
from models import UserModel, UserTable
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler

from .common import Ctx


@require_user_data
async def toggle_user_block(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    keyboard = update.effective_message.reply_markup.inline_keyboard
    new_keyboard = []

    uid = update.callback_query.data.split('#')[-1]
    target_user = await user_get(UserTable.user_id == int(uid))
    was_blocked = False

    if not target_user:
        await update.effective_message.reply_text('کاربر پیدا نشد. ❌')
        await update.effective_message.edit_reply_markup()
        return

    if state.block_list.pop(uid, False):
        await update.effective_message.reply_text(
            'کاربر آزادسازی گردید. 🟢'
        )
        was_blocked = True

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

    for X in keyboard:
        row = []
        for Y in X:
            t, *_ = Y.callback_data.split('#')
            if t == 'toggle_user_block':
                if was_blocked:
                    text = 'آزاد سازی 🟢'
                else:
                    text = 'بلاک ⛔'

                row.append(InlineKeyboardButton(
                    callback_data=Y.callback_data,
                    text=text
                ))
            else:
                row.append(Y)

        new_keyboard.append(row)

    await update.effective_message.edit_reply_markup(
        InlineKeyboardMarkup(new_keyboard)
    )


H_BLOCK = [
    CallbackQueryHandler(
        toggle_user_block,
        pattern='^toggle_user_block#[0-9]+$',
        block=False
    ),
]
