
from db.user import user_get, user_update
from deps import require_user_data
from models import UserModel, UserTable
from settings import KW_SAVELST
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters

from .common import Ctx


@require_user_data
async def show_saved_users(update: Update, ctx: Ctx, state: UserModel):

    if not state.saved_list:
        await update.effective_message.reply_text(
            'شما کاربری را ذخیر نکرده اید.'
        )
        return

    keyboard = []
    for uid, data in state.saved_list.items():
        keyboard.append([
            InlineKeyboardButton(
                'حذف کاربر ❌',
                callback_data=(
                    f'remove_saved_user#{uid}'
                )
            ),
            InlineKeyboardButton(
                data['name'],
                url=f't.me/{ctx.bot.username}?start={data["codename"]}'
            )
        ])

    await update.effective_message.reply_text(
        'کاربران ذخیره شده شما.',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@require_user_data
async def toggle_saved_user(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    keyboard = update.effective_message.reply_markup.inline_keyboard
    new_keyboard = []

    uid = update.callback_query.data.split('#')[-1]
    target_user = await user_get(UserTable.user_id == int(uid))
    text = 'حذف کاربر ❌'

    if not target_user:
        await update.effective_message.reply_text('کاربر پیدا نشد. ❌')
        await update.effective_message.edit_reply_markup()
        return

    if state.saved_list.pop(uid, False):
        await update.effective_message.reply_text(
            'کاربر از لیست حذف شد. 🔴'
        )
        text = 'ذخیر کاربر ⭐'
    else:
        if len(state.saved_list.keys()) >= 10:
            await update.effective_message.reply_text(
                'حداکثر تعداد کاربران ذخیره شده 10 نفر می باشد. ❌'
            )
            return

        state.saved_list[uid] = {
            'codename': target_user.codename,
            'name': target_user.name,
        }
        await update.effective_message.reply_text(
            'کاربر ذخیره شد. ⭐'
        )

    await user_update(
        UserTable.user_id == state.user_id,
        saved_list=state.saved_list
    )

    for X in keyboard:
        row = []
        for Y in X:
            t, *_ = Y.callback_data.split('#')
            if t == 'remove_saved_user' or t == 'save_user':
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


H_SAVE = [
    CallbackQueryHandler(
        toggle_saved_user,
        pattern='^(remove_saved_user|save_user)#[0-9]+$',
        block=False
    ),
    MessageHandler(
        filters.Text([KW_SAVELST]),
        show_saved_users, block=False,
    ),
]
