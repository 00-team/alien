

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

    uid = int(update.callback_query.data.split('#')[-1])

    msg = await update.effective_message.reply_text(
        'پیام خود را ارسال کنید:',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_direct_message'
        )]])
    )

    ctx.user_data['to_user_id'] = uid
    ctx.user_data['send_direct_msg_id'] = msg.id

    return 'GET_MESSAGE'


@require_user_data
async def handle_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    error_msg_id = ctx.user_data.get('handle_dirt_msg_err_msg_id')

    to_user_id = ctx.user_data.get('to_user_id')
    if to_user_id is None:
        return

    direct_id = await add_direct(
        to_user_id,
        update.effective_user.id,
        update.effective_message.id
    )

    if not direct_id:
        return

    nseen_count = await get_direct_notseen_count(to_user_id)
    keyboard = [InlineKeyboardButton(
        'مشاهده 👀', callback_data=f'show_direct#{direct_id}'
    )]

    if nseen_count > 1:
        keyboard.append(InlineKeyboardButton(
            'مشاهده همه 📭',
            callback_data='show_direct#all'
        ))

    user_b = await get_user(user_id=to_user_id)
    if user_b and user_b.direct_msg_id:
        await ctx.bot.delete_message(to_user_id, user_b.direct_msg_id)

    msg = await ctx.bot.send_message(
        to_user_id,
        f'شما یک پیام جدید دارید!\n\n {nseen_count} پیام خوانده نشده.\n.',
        reply_markup=InlineKeyboardMarkup([keyboard])
    )
    await update_user(to_user_id, direct_msg_id=msg.id)

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

    user_id = update.effective_user.id
    chat_id = update.effective_message.chat_id

    if not direct:
        await update.effective_message.reply_text('خطا در دریافت پیام! ❌')
        return

    msg_id = await ctx.bot.copy_message(
        chat_id, direct.sender_id, direct.message_id,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'پاسخ ✍', callback_data='direct_reply#xx'
            ),
            InlineKeyboardButton(
                'بلاک ⛔', callback_data='block_user#xx'
            ),
        ]])
    )

    if msg_id and not direct.seen:
        await ctx.bot.send_message(
            direct.sender_id, 'پیام شما مشاهده شد. 🧉',
            reply_to_message_id=direct.message_id
        )
        await update_direct(direct.direct_id, user_id, seen=True)

    if not msg_id:
        await update.effective_message.reply_text('خطا در دریافت پیام! ❌')


@require_user_data
async def show_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    await update.callback_query.answer()

    user_id = update.effective_user.id

    direct_id = update.callback_query.data.split('#')[-1]
    # if direct_id == 'all':
    #     directs = await get_direct_notseen(user_id)
    #     for direct in directs:
    #         await send_show_direct(update, ctx, direct)
    #         time.sleep(5)

    # else:
    direct = await get_direct(int(direct_id), user_id)
    await send_show_direct(update, ctx, direct)


@require_user_data
async def send_not_seen_messages(update: Update, ctx: Ctx, _: UserModel):
    user_id = update.effective_user.id
    directs = await get_direct_notseen(user_id)

    for direct in directs:
        await send_show_direct(update, ctx, direct)
        time.sleep(5)


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
