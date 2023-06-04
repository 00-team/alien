

import logging
import time

from database import add_direct, get_direct, get_direct_notseen
from database import get_direct_notseen_count, get_user, update_direct
from database import update_user
from dependencies import require_user_data
from models import DirectModel, UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest, Forbidden, TimedOut
from telegram.ext import ContextTypes, ConversationHandler
from utils import config

from .channels import require_joined

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def send_direct_message(update: Update, ctx: Ctx, user_data: UserModel):
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
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_direct_message'
        )]])
    )

    ctx.user_data['direct_send_type'] = send_type
    ctx.user_data['direct_send_id'] = send_id

    ctx.user_data['send_direct_msg_id'] = msg.id

    return 'GET_MESSAGE'


@require_user_data
async def handle_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    error_msg_id = ctx.user_data.get('handle_dirt_msg_err_msg_id')
    user = update.effective_user
    msg = update.effective_message

    send_type = ctx.user_data.pop('direct_send_type', None)
    send_id = ctx.user_data.pop('direct_send_id', None)
    receiver_id = None

    if send_type is None or send_id is None:
        logging.info(f'{send_type=} - {send_id=}')
        return

    if send_type == 'direct_reply':
        direct = await get_direct(send_id)
        if not direct:
            logging.info(f'direct to reply not found: {send_id=}')
            return

        direct_id = await add_direct(
            direct.sender_id,
            user.id,
            msg.id,
            reply_to=direct.direct_id
        )
        receiver_id = direct.sender_id

    elif send_type == 'send_direct_message':
        direct_id = await add_direct(
            send_id,
            update.effective_user.id,
            update.effective_message.id
        )
        receiver_id = send_id

    if not direct_id or not receiver_id:
        logging.info(f'no {direct_id=} or {receiver_id=}')
        return

    nseen_count = await get_direct_notseen_count(receiver_id)
    keyboard = [InlineKeyboardButton(
        'مشاهده 👀', callback_data=f'show_direct#{direct_id}'
    )]

    if nseen_count > 1:
        keyboard.append(InlineKeyboardButton(
            'مشاهده همه 📭',
            callback_data='show_direct#all'
        ))

    user_b = await get_user(user_id=receiver_id)
    if user_b and user_b.direct_msg_id:
        try:
            await ctx.bot.delete_message(receiver_id, user_b.direct_msg_id)
        except Exception:
            pass

    try:
        msg = await ctx.bot.send_message(
            receiver_id,
            f'شما یک پیام جدید دارید!\n\n {nseen_count} پیام خوانده نشده.\n.',
            reply_markup=InlineKeyboardMarkup([keyboard])
        )
        await update_user(receiver_id, direct_msg_id=msg.id)

        await update.effective_message.reply_text(
            'پیام شما به صورت ناشناس ارسال شد. ✅'
        )
    except TimedOut:
        pass
    except Exception as e:
        logging.exception(e)

    chat_id = update.effective_message.chat_id

    send_msg_id = ctx.user_data.pop('send_direct_msg_id', None)

    if send_msg_id:
        try:
            await ctx.bot.delete_message(chat_id, send_msg_id)
        except TimedOut:
            pass
        except Exception as e:
            logging.exception(e)

    if error_msg_id:
        ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)
        try:
            await ctx.bot.delete_message(chat_id, error_msg_id)
        except TimedOut:
            pass
        except Exception as e:
            logging.exception(e)

    return ConversationHandler.END


@require_user_data
async def cancel_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    await update.callback_query.answer()

    chat_id = update.effective_message.chat_id
    msg_id = ctx.user_data.pop('send_direct_msg_id', None)
    error_msg_id = ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)

    if msg_id:
        try:
            await ctx.bot.delete_message(chat_id, msg_id)
        except TimedOut:
            pass
        except Exception as e:
            logging.exception(e)

    if error_msg_id:
        try:
            await ctx.bot.delete_message(chat_id, error_msg_id)
        except TimedOut:
            pass
        except Exception as e:
            logging.exception(e)

    return ConversationHandler.END
