
import logging
import random
import time

from db.user import user_count, user_update
from deps import require_admin
from models import UserModel, UserTable
from settings import sqlx
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.ext import ConversationHandler, MessageHandler, filters

Ctx = ContextTypes.DEFAULT_TYPE


JOB_ID = 'admin_sendall_msg'


@require_admin
async def sendall(update: Update, ctx: Ctx):
    if ctx.job_queue.get_jobs_by_name(JOB_ID):
        await update.effective_message.reply_text('job already in queue. 🤡')
        return

    await update.effective_message.reply_text(
        'send any message 🐧',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'Cancel ❌',
                callback_data='cancel_sendall_admin'
            )
        ]])
    )

    return 'ADMIN_SEND_ALL_MESSAGE'


async def sendall_job(ctx: Ctx):
    logging.info('sending a message to all users')

    all_users = await sqlx.fetch_all(
        select(UserTable)
        .where(UserTable.blocked_bot == False)
    )
    data = {
        'success': 0,
        'blocked': 0,
        'error': 0,
        'timeout': 0,
    }

    msg_id = ctx.job.data['msg_id']
    limit = ctx.job.data['limit']

    if limit and limit < len(all_users):
        random.shuffle(all_users)
        all_users = all_users[:limit]

    for U in all_users:
        time.sleep(0.1)
        target = UserModel(**U)

        try:
            msg_id = await ctx.bot.copy_message(
                target.user_id, ctx.job.user_id, msg_id,
            )
            data['success'] += 1
        except RetryAfter as e:
            time.sleep(e.retry_after + 10)
            logging.info(f'[send_all]: retry_after {e.retry_after}')
            data['timeout'] += 1
        except Forbidden:
            logging.info(
                f'[send_all]: forbidden {target.user_id} - {target.name}'
            )
            data['blocked'] += 1
            await user_update(
                UserTable.user_id == target.user_id,
                blocked_bot=True
            )
        except NetworkError:
            data['error'] += 1
        except TelegramError as e:
            logging.exception(e)
            data['error'] += 1

    time.sleep(2)
    stats = (
        'send to all done.\n'
        f'success: {data["success"]}\n'
        f'blocked: {data["blocked"]}\n'
        f'error: {data["error"]}\n'
        f'timeout: {data["timeout"]}\n'
    )
    logging.info(stats)
    await ctx.bot.send_message(ctx.job.user_id, stats)


@require_admin
async def sendall_message(update: Update, ctx: Ctx):
    if ctx.job_queue.get_jobs_by_name(JOB_ID):
        await update.effective_message.reply_text('job already in queue. 🤡')
        return

    msg = update.effective_message

    total_users = await user_count(True)
    limit = 0

    ctx.job_queue.run_once(
        sendall_job, 30,
        chat_id=msg.chat.id,
        user_id=update.effective_user.id,
        data={
            'msg_id': msg.message_id,
            'limit': limit
        },
        name=JOB_ID
    )

    limit = limit or total_users

    await msg.reply_text(
        '✅ پیام شما ذخیره شد ، پیام شما به '
        f'{limit}/{total_users} نفر ارسال خواهد شد .',
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'Cancel ❌',
                callback_data='cancel_sendall_admin'
            )
        ]])
    )


@require_admin
async def cancel(update: Update, ctx: Ctx):
    jbs = ctx.job_queue.get_jobs_by_name(JOB_ID)
    stoped = False
    for j in jbs:
        j.schedule_removal()
        stoped = True

    if stoped:
        text = 'send all was stoped ✅'
    else:
        text = 'send all job was not found ❌'

    await update.effective_message.reply_text(text)
    return ConversationHandler.END


H_SENDALL_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        CommandHandler(['sendall'], sendall)
    ],
    states={
        'ADMIN_SEND_ALL_MESSAGE': [
            MessageHandler(
                filters.ChatType.PRIVATE,
                sendall_message,
            )
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            cancel,
            pattern='^cancel_sendall_admin$'
        )
    ],
)
