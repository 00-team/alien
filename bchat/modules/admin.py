

import logging
import random
import time

from database import get_user, get_user_count, update_user
from db.direct import direct_add
from deps import require_admin
from models import UserModel, UserTable
from modules.common import delete_message
from settings import database
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
from telegram.error import TimedOut
from telegram.ext import CommandHandler, ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


@require_admin
async def get_file_id(update: Update, ctx: Ctx):
    if update.message.photo:
        await update.message.reply_html(
            'photo: \n'
            f'<code>{update.message.photo[0].file_id}</code>'
        )

    if update.message.video:
        await update.message.reply_html(
            'video: \n'
            f'<code>{update.message.video.file_id}</code>'
        )

    if update.message.animation:
        await update.message.reply_html(
            'animation: \n'
            f'<code>{update.message.animation.file_id}</code>'
        )


@require_admin
async def get_user_score(update: Update, ctx: Ctx):
    if not ctx.args:
        await update.effective_message.reply_text(
            'Error ❌\n/user_score <code>\n'
            '/user_score <code> set 12'
        )
        return

    user_data = await get_user(None, ctx.args[0])
    if user_data is None:
        await update.effective_message.reply_text(
            f'Error ❌\nuser with code {ctx.args[0]} was not found'
        )
        return

    await update.effective_message.reply_html(
        'User: \n'
        f'    id: <code>{user_data.user_id}</code>\n'
        f'    name: {user_data.name}\n'
        f'    total score: {user_data.total_score}\n'
        f'    used  score: {user_data.used_score}'
    )

    if len(ctx.args) >= 3 and ctx.args[1] == 'set':
        try:
            if len(ctx.args) > 3 and ctx.args[3] == 'total':
                await update_user(
                    user_data.user_id, total_score=int(ctx.args[2])
                )
            else:
                new_score = min(int(ctx.args[2]), user_data.total_score)
                await update_user(
                    user_data.user_id,
                    used_score=new_score
                )
            await update.effective_message.reply_text(
                'Ok ✅\nuser score was updated'
            )
        except Exception:
            await update.effective_message.reply_text(
                f'Error ❌\ninvalid score: {ctx.args[2]}'
            )


@require_admin
async def stats(update: Update, ctx: Ctx):
    users = await get_user_count()
    await update.effective_message.reply_text(
        f'total users: {users}'
    )


@require_admin
async def help_cmd(update: Update, ctx: Ctx):
    await update.effective_message.reply_text(
        '/help -> for this message\n'
        '/stats -> user count\n'
        '/user_score <code> -> get the user score\n'
        '/user_score <code> set 12 -> set the user used score\n'
        '/user_score <code> set 12 total -> set the user total score\n'
        '/channels -> get list of channels\n---\n'
        '/send_direct_to_all\n'
        'limit=(69)\n\n'
        'hi\n---\n'
        '/cancel_send_direct_all -> ...'
    )


async def send_direct_to_all_job(ctx: Ctx):
    logging.info('sending a message to all users')

    all_users = await database.fetch_all(
        select(UserTable)
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
        direct_id = await direct_add(
            user_id=target.user_id,
            sender_id=ctx.job.user_id,
            message_id=msg_id,
            from_admin=True
        )

        keyboard = [InlineKeyboardButton(
            'مشاهده 👀', callback_data=f'show_direct#{direct_id}'
        )]

        # if target.direct_msg_id:
        #     await delete_message(ctx, target.user_id, target.direct_msg_id)

        try:
            msg = await ctx.bot.send_message(
                target.user_id,
                'شما یک پیام جدید دارید!',
                reply_markup=InlineKeyboardMarkup([keyboard])
            )
            await update_user(target.user_id, direct_msg_id=msg.id)

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
async def send_direct_to_all(update: Update, ctx: Ctx):
    text = update.effective_message.text[19:]
    limit = None

    limit_idx = text.find('limit=(')

    if limit_idx > -1:
        limit = text[limit_idx + 7:]
        limit_end = limit.find(')')
        limit = limit[:limit_end]

        text = text[limit_idx+7+limit_end+1:]

    if limit:
        try:
            limit = int(limit)
        except Exception:
            limit = None

    if not text:
        await update.effective_message.reply_text('Empty Message ❌')

    msg = await update.effective_message.reply_text(text)
    total_users = await get_user_count()

    await update.effective_message.reply_text(
        f'limit is: {limit}\n'
        'you have 30s to cancel this.\n'
        '/cancel_send_direct_all'
    )

    if ctx.job_queue.get_jobs_by_name('send_direct_to_all'):
        await update.effective_message.reply_text('job already in queue. 🤡')
        return

    ctx.job_queue.run_once(
        send_direct_to_all_job, 30,
        chat_id=msg.chat.id,
        user_id=update.effective_user.id,
        data={
            'msg_id': msg.message_id,
            'limit': limit
        },
        name='send_direct_to_all'
    )

    limit = limit or total_users

    await msg.reply_text(
        '✅ پیام شما ذخیره شد ، پیام شما به '
        f'{limit}/{total_users} نفر ارسال خواهد شد .'
    )


@require_admin
async def cancel_send_direct_all(update: Update, ctx: Ctx):
    jbs = ctx.job_queue.get_jobs_by_name('send_direct_to_all')
    for j in jbs:
        j.schedule_removal()

    await update.effective_message.reply_text(
        'send direct to all was stoped.'
    )


async def send_user_info(update: Update, ctx: Ctx, user_id: int):
    try:
        chat = await ctx.bot.get_chat(user_id)

        await update.effective_message.reply_text(
            f'USERS INFO:\n'
            f'id: {chat.id}\n'
            f'name: {chat.full_name}\n'
            f'username: @{chat.username}\n',
        )
    except TimedOut:
        pass
    except Exception as e:
        logging.exception(e)


HANDLERS_ADMIN = [
    CommandHandler(['stats'], stats),
    CommandHandler(['user_score'], get_user_score),
    CommandHandler(['help'], help_cmd),
    CommandHandler(
        ['send_direct_to_all'], send_direct_to_all
    ),
    CommandHandler(
        ['cancel_send_direct_all'], cancel_send_direct_all
    ),
]
