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


JOB_ID = 'admin_get_usernames'


async def get_usernames_job(ctx: Ctx):
    logging.info('getting all the users usernames')

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

    for U in all_users:
        time.sleep(0.1)
        target = UserModel(**U)

        try:
            user_chat = await ctx.bot.get_chat(chat_id=target.user_id)
            un = None
            if user_chat.username:
                un = user_chat.username.lower()
            await user_update(
                UserTable.user_id == target.user_id,
                username=un
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
        'get usersnames.\n'
        f'success: {data["success"]}\n'
        f'blocked: {data["blocked"]}\n'
        f'error: {data["error"]}\n'
        f'timeout: {data["timeout"]}\n'
    )
    logging.info(stats)
    await ctx.bot.send_message(ctx.job.user_id, stats)


@require_admin
async def get_all_usernames(update: Update, ctx: Ctx):

    if ctx.job_queue.get_jobs_by_name(JOB_ID):
        await update.effective_message.reply_text('job already in queue. 🤡')
        return

    msg = update.effective_message
    total_users = await user_count(True)

    ctx.job_queue.run_once(
        get_usernames_job, 10,
        chat_id=msg.chat.id,
        user_id=update.effective_user.id,
        name=JOB_ID
    )

    await msg.reply_text(f'starting the job...: {total_users}')


H_GETUN = [
    CommandHandler(['getuns'], get_all_usernames)
]
