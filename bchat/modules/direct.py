

import logging
import time

from database import add_direct, get_direct, get_direct_notseen
from database import get_direct_notseen_count, get_user, update_direct
from database import update_user
from dependencies import require_user_data
from models import DirectModel, UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def send_direct_message(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    send_type, send_id = update.callback_query.data.split('#')
    send_id = int(send_id)

    msg = await update.effective_message.reply_text(
        'پیام خود را ارسال کنید:',
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
        return

    if send_type == 'direct_reply':
        direct = await get_direct(send_id)
        if not direct:
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
        await ctx.bot.delete_message(receiver_id, user_b.direct_msg_id)

    msg = await ctx.bot.send_message(
        receiver_id,
        f'شما یک پیام جدید دارید!\n\n {nseen_count} پیام خوانده نشده.\n.',
        reply_markup=InlineKeyboardMarkup([keyboard])
    )
    await update_user(receiver_id, direct_msg_id=msg.id)

    await update.effective_message.reply_text(
        'پیام شما به صورت ناشناس ارسال شد. ✅'
    )

    chat_id = update.effective_message.chat_id

    send_msg_id = ctx.user_data.pop('send_direct_msg_id', None)

    if send_msg_id:
        await ctx.bot.delete_message(chat_id, send_msg_id)

    if error_msg_id:
        ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)
        await ctx.bot.delete_message(chat_id, error_msg_id)

    return ConversationHandler.END


async def send_show_direct(update: Update, ctx: Ctx, direct: DirectModel):

    chat_id = update.effective_message.chat_id

    if not direct:
        await update.effective_message.reply_text('خطا در دریافت پیام! ❌')
        return

    repdir_mid = None

    if direct.reply_to:
        repdir = await get_direct(direct.reply_to)
        if repdir:
            repdir_mid = repdir.message_id

    msg_id = await ctx.bot.copy_message(
        chat_id, direct.sender_id, direct.message_id,
        reply_to_message_id=repdir_mid,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'پاسخ ✍', callback_data=f'direct_reply#{direct.direct_id}'
            ),
            InlineKeyboardButton(
                'بلاک ⛔', callback_data=f'toggle_user_block#{direct.sender_id}'
            ),
        ]])
    )

    if msg_id and not direct.seen:
        await ctx.bot.send_message(
            direct.sender_id, 'پیام شما مشاهده شد. 🧉',
            reply_to_message_id=direct.message_id
        )
        await update_direct(direct.direct_id, seen=True)

    if not msg_id:
        await update.effective_message.reply_text('خطا در دریافت پیام! ❌')


@require_user_data
async def show_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    await update.callback_query.answer()

    direct_id = update.callback_query.data.split('#')[-1]

    direct = await get_direct(int(direct_id))
    await send_show_direct(update, ctx, direct)


@require_user_data
async def send_not_seen_messages(update: Update, ctx: Ctx, _: UserModel):
    if update.callback_query:
        update.callback_query.answer()

    user_id = update.effective_user.id
    directs = await get_direct_notseen(user_id)

    if not directs:
        await update.effective_message.reply_text(
            'پیامی یافت نشد! 🧊'
        )
        return

    if update.callback_query:
        await update.effective_message.delete()

    for direct in directs:
        await send_show_direct(update, ctx, direct)
        time.sleep(1)


@require_user_data
async def cancel_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    await update.callback_query.answer()

    chat_id = update.effective_message.chat_id
    msg_id = ctx.user_data.pop('send_direct_msg_id', None)
    error_msg_id = ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)

    if msg_id:
        await ctx.bot.delete_message(chat_id, msg_id)

    if error_msg_id:
        await ctx.bot.delete_message(chat_id, error_msg_id)

    return ConversationHandler.END
