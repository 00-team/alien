

import logging

from database import add_direct
from dependencies import require_user_data
from models import UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def send_direct_message(update: Update, ctx: Ctx, user_data: UserModel):
    logging.info('in send_direct_message')
    await update.callback_query.answer()

    logging.info(update.callback_query.data)

    uid = int(update.callback_query.data.split('#')[-1])

    msg_id = await update.effective_message.reply_text(
        'پیام خود را ارسال کنید:',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_direct_message'
        )]])
    )

    ctx.user_data['to_user_id'] = uid
    ctx.user_data['send_direct_msg_id'] = msg_id

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

    await ctx.bot.send_message(
        to_user_id,
        'شما یک پیام جدید دارید!',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'مشاهده 👀',
                callback_data=f'show_direct#{direct_id}'
            ),
            # InlineKeyboardButton('پاسخ ✍', callback_data='direct_reply#xx'),
            # InlineKeyboardButton('بلاک ⛔', callback_data='block_user#xx'),
        ]])
    )

    logging.info('GG')

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


@require_user_data
async def cancel_direct_message(update: Update, ctx: Ctx, usr_data: UserModel):
    chat_id = update.effective_message.chat_id
    msg_id = ctx.user_data.pop('send_direct_msg_id', None)
    error_msg_id = ctx.user_data.pop('handle_dirt_msg_err_msg_id', None)

    if msg_id:
        await ctx.bot.delete_message(chat_id, msg_id)

    if error_msg_id:
        await ctx.bot.delete_message(chat_id, error_msg_id)

    return ConversationHandler.END
