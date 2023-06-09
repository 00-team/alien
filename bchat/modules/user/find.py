

import logging

from db.user import user_get
from deps import require_user_data
from models.user import GENDER_DISPLAY, UserModel, UserTable
from settings import KW_CTSPLCN
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram import Update
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

    return 'FIND_USER'


@require_user_data
async def find_user(update: Update, ctx: Ctx, state: UserModel):
    logging.info(update.to_dict())
    msg = update.effective_message

    target_username = None
    target_user_id = None
    target = None

    for e in msg.entities:
        if e.type == MessageEntity.MENTION:
            target_username = msg.text[e.offset+1:e.offset+e.length]
            break

    if msg.forward_from and not msg.forward_from.is_bot:
        target_user_id = msg.forward_from.id

    logging.info(f'\n{target_user_id=}\n{target_username=}\n')

    if target_username:
        target = await user_get(UserTable.username == target_username)
    elif target_user_id:
        target = await user_get(UserTable.user_id == target_user_id)

    if not target:
        await update.effective_message.reply_text(
            'کاربر یافت نشد 😢',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    'لغو ❌', callback_data='cancel_find_user'
                )
            ]])
        )
        return

    await msg.reply_text(f'{target_username=}\n{target_user_id=}')
    text = (
        f'نام: {target.name}\n'
        f'جنسیت: {GENDER_DISPLAY[target.gender]}\n'
        f'سن: {target.age}\n'
    )

    trail_text = '\n\n👇 دکمه ارسال پیام رو بزن و بعدش پیامت رو ارسال کن.'

    keyboard = []
    if str(target.user_id) in state.saved_list:
        keyboard.append(InlineKeyboardButton(
            'حذف کاربر ❌',
            callback_data=(
                f'remove_saved_user#{target.user_id}'
            )
        ))
    else:
        if len(state.saved_list.keys()) < 10:
            keyboard.append(InlineKeyboardButton(
                'ذخیر کاربر ⭐',
                callback_data=(
                    f'save_user#{target.user_id}'
                )
            ))

    if str(state.user_id) not in target.block_list:
        keyboard.append(InlineKeyboardButton(
            'ارسال پیام ✉',
            callback_data=(
                f'send_direct_message#{target.user_id}'
            )
        ))
    else:
        trail_text = (
            '\n\nاین کاربر شما را بلاک کرده. ⛔'
        )

    file_id = config['default_profile_picture']
    if target.picture:
        file_id = target.picture

    await update.effective_message.reply_photo(
        file_id, text + trail_text,
        reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
    )

    return ConversationHandler.END


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
