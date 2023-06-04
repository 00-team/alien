

import logging

from db.direct import direct_add, direct_get, direct_unseen_count
from db.user import user_get, user_update
from deps import require_user_data
from models import DirectTable, UserModel, UserTable
from modules.common import delete_message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler, filters

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def send_direct_message(update: Update, ctx: Ctx, _):
    await update.callback_query.answer()

    send_type, send_id = update.callback_query.data.split('#')
    send_id = int(send_id)
    reply_to_msg_id = None
    text = 'پیام خود را ارسال کنید:'

    if send_type == 'direct_reply':
        reply_to_msg_id = update.effective_message.id
        text = (
            '☝️ در حال پاسخ دادن به فرستنده این '
            'پیام هستی ... ؛ منتظریم بفرستی :)'
        )

    msg = await update.effective_message.reply_text(
        text,
        reply_to_message_id=reply_to_msg_id,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'لغو ❌', callback_data='cancel_direct_message'
            )
        ]])
    )

    ctx.user_data['direct_send_type'] = send_type
    ctx.user_data['direct_send_id'] = send_id
    ctx.user_data['send_direct_msg_id'] = msg.id

    return 'GET_MESSAGE'


@require_user_data
async def handle_direct_message(update: Update, ctx: Ctx, state: UserModel):
    error_msg_id = ctx.user_data.get('handle_dirt_msg_err_msg_id')
    user = update.effective_user
    msg = update.effective_message
    chat_id = update.effective_message.chat_id

    send_type = ctx.user_data.pop('direct_send_type', None)
    send_id = ctx.user_data.pop('direct_send_id', None)
    receiver_id = None

    if send_type is None or send_id is None:
        logging.info(f'{send_type=} - {send_id=}')
        return

    if send_type == 'direct_reply':
        direct = await direct_get(DirectTable.direct_id == send_id, limit=1)
        if not direct:
            logging.info(f'direct to reply not found: {send_id=}')
            return

        direct_id = await direct_add(
            user_id=direct.sender_id,
            sender_id=user.id,
            message_id=msg.id,
            reply_to=direct.direct_id
        )
        receiver_id = direct.sender_id

    elif send_type == 'send_direct_message':
        direct_id = await direct_add(
            user_id=send_id,
            sender_id=user.id,
            message_id=msg.id
        )
        receiver_id = send_id

    if not direct_id or not receiver_id:
        logging.info(f'no {direct_id=} or {receiver_id=}')
        return

    unseen_count = await direct_unseen_count(receiver_id)
    keyboard = [InlineKeyboardButton(
        'مشاهده 👀', callback_data=f'show_direct#{direct_id}'
    )]

    if unseen_count > 1:
        keyboard.append(InlineKeyboardButton(
            'مشاهده همه 📭',
            callback_data='show_direct#all'
        ))

    target = await user_get(UserTable.user_id == receiver_id)
    if target and target.direct_msg_id:
        await delete_message(ctx, receiver_id, target.direct_msg_id)

    try:
        new_msg = await ctx.bot.send_message(
            receiver_id,
            f'شما یک پیام جدید دارید!\n\n {unseen_count} پیام خوانده نشده.\n.',
            reply_markup=InlineKeyboardMarkup([keyboard])
        )
        await user_update(
            UserTable.user_id == receiver_id,
            direct_msg_id=new_msg.id
        )
        await update.effective_message.reply_text(
            'پیام شما به صورت ناشناس ارسال شد. ✅'
        )
    except Forbidden:
        await update.effective_message.reply_text(
            'این کاربر ربات را ترک کرده. ❌'
        )
    except Exception as e:
        logging.exception(e)

    send_msg_id = ctx.user_data.pop('send_direct_msg_id', None)

    if send_msg_id:
        await delete_message(ctx, chat_id, send_msg_id)

    if error_msg_id:
        ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)
        await delete_message(ctx, chat_id, error_msg_id)

    return ConversationHandler.END


@require_user_data
async def cancel_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    await update.callback_query.answer()

    chat_id = update.effective_message.chat_id
    msg_id = ctx.user_data.pop('send_direct_msg_id', None)
    error_msg_id = ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)

    if msg_id:
        await delete_message(ctx, chat_id, msg_id)

    if error_msg_id:
        await delete_message(ctx, chat_id, error_msg_id)

    return ConversationHandler.END


H_SEND_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        CallbackQueryHandler(
            send_direct_message,
            pattern='^(send_direct_message|direct_reply)#(.*)$'
        )
    ],
    states={
        'GET_MESSAGE': [
            MessageHandler(
                filters.ChatType.PRIVATE,
                handle_direct_message,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            cancel_direct_message,
            pattern='^cancel_direct_message$'
        )
    ],
)
