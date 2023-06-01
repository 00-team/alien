

import logging
import time

from database import add_direct, get_direct_notseen_count, get_user
from database import get_user_count, update_user
from dependencies import require_admin
from models import UserModel, Users
from settings import database
from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
from telegram.ext import ContextTypes, ConversationHandler

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
        '/channels -> get list of channels\n'
        '/send_direct_to_all -> ...'
    )


@require_admin
async def cancel(update: Update, ctx: Ctx):
    await update.effective_message.reply_text('canceled.')
    return ConversationHandler.END


async def send_direct_to_all_job(ctx: Ctx):
    all_users = await database.fetch_all(
        select(Users)
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
        direct_id = await add_direct(
            target.user_id,
            ctx.job.user_id,
            ctx.job.data,
        )

        nseen_count = await get_direct_notseen_count(target.user_id)
        keyboard = [InlineKeyboardButton(
            'مشاهده 👀', callback_data=f'show_direct#{direct_id}'
        )]

        if nseen_count > 1:
            keyboard.append(InlineKeyboardButton(
                'مشاهده همه 📭',
                callback_data='show_direct#all'
            ))

        if target.direct_msg_id:
            try:
                await ctx.bot.delete_message(
                    target.user_id, target.direct_msg_id
                )
            except Exception as e:
                logging.exception(e)

        try:
            msg = await ctx.bot.send_message(
                target.user_id,
                'شما یک پیام جدید دارید!\n\n'
                f' {nseen_count} پیام خوانده نشده.\n.',
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
    await ctx.bot.send_message(ctx.job.user_id, (
        'send to all done.\n'
        f'success: {data["success"]}\n'
        f'blocked: {data["blocked"]}\n'
        f'error: {data["error"]}\n'
        f'timeout: {data["timeout"]}\n'
    ))


@require_admin
async def send_direct_to_all(update: Update, ctx: Ctx):

    text = update.effective_message.text[19:]
    if not text:
        await update.effective_message.reply_text('Empty Message ❌')

    msg = await update.effective_message.reply_text(text)
    total_users = await get_user_count()

    ctx.job_queue.run_once(
        send_direct_to_all_job, 1,
        chat_id=msg.chat.id,
        user_id=update.effective_user.id,
        data=msg.message_id,
        name='send_direct_to_all'
    )
    await msg.reply_text(
        f'✅ پیام شما ذخیره شد ، پیام شما به {total_users} نفر ارسال خواهد شد .'
    )
