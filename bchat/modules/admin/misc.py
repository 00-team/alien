
import logging
import random
import time

from db.direct import direct_add, direct_get, direct_unseen_count
from db.direct import direct_update
from db.user import user_count, user_get, user_update
from deps import require_admin, require_user_data
from models import DirectTable, UserModel, UserTable
from settings import sqlx
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
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

    user_data = await user_get(UserTable.codename == ctx.args[0])

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
                await user_update(
                    UserTable.user_id == user_data.user_id,
                    total_score=int(ctx.args[2])
                )
            else:
                new_score = min(int(ctx.args[2]), user_data.total_score)
                await user_update(
                    UserTable.user_id == user_data.user_id,
                    used_score=new_score,
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
    total = await user_count(False)
    active = await user_count(True)

    await update.effective_message.reply_text(
        f'total users: {active}/{total}'
    )


@require_admin
async def help_cmd(update: Update, ctx: Ctx):
    await update.effective_message.reply_text(
        '/help -> for this message\n'
        '/stats -> user count\n'
        '/update_db -> only for developer\n'
        '/seen_all -> seen all of your directs\n'
        '/charge <Toman> <code> <code> ...\n'
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
            await user_update(
                UserTable.user_id == target.user_id,
                direct_msg_id=msg.id
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
async def send_direct_to_all(update: Update, ctx: Ctx):

    if ctx.job_queue.get_jobs_by_name('send_direct_to_all'):
        await update.effective_message.reply_text('job already in queue. 🤡')
        return

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
    total_users = await user_count(True)

    await update.effective_message.reply_text(
        f'limit is: {limit}\n'
        'you have 30s to cancel this.\n'
        '/cancel_send_direct_all'
    )

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


@require_admin
@require_user_data
async def seen_all(update: Update, ctx: Ctx, state: UserModel):
    user = update.effective_user
    limit = 500
    total = await direct_unseen_count(user.id)

    try:
        limit = max(int(ctx.args[0]), 2)
    except Exception:
        pass

    directs = await direct_get(
        DirectTable.user_id == user.id,
        DirectTable.seen == False,
        limit=limit
    )

    await update.effective_message.reply_text(
        f'loaded {len(directs)}/{total} directs.'
    )
    success = 0
    errors = 0

    for direct in directs:
        try:
            await direct_update(
                DirectTable.direct_id == direct.direct_id,
                seen=True
            )
            await ctx.bot.send_message(
                direct.sender_id, 'پیام شما مشاهده شد. 🧉',
                reply_to_message_id=direct.message_id
            )
            success += 1
        except Exception:
            errors += 1

        time.sleep(0.1)

    await update.effective_message.reply_text(
        f'success: {success}\nerrors: {errors}'
    )


@require_admin
async def update_db(update: Update, ctx: Ctx):
    await update.effective_message.reply_text('nothing to do.')


H_MISC = [
    CommandHandler(['stats'], stats),
    CommandHandler(['update_db'], update_db, block=False),
    CommandHandler(['seen_all'], seen_all),
    CommandHandler(['user_score'], get_user_score),
    CommandHandler(['help'], help_cmd),
    CommandHandler(
        ['send_direct_to_all'], send_direct_to_all
    ),
    CommandHandler(
        ['cancel_send_direct_all'], cancel_send_direct_all
    ),
]
