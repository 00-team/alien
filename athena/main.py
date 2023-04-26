

import logging
import sys
from time import sleep

import shared.logger
from modules.admin import error_handler, help_command, users
from modules.chat import chat_member_update, my_chat_update
from shared.database import channel_remove, channel_set_limit, channel_toggle
from shared.database import check_user, get_keyboard_chats, get_users
from shared.database import is_forwards_enable, setup_databases
from shared.database import toggle_forwards, user_remove
from shared.dependencies import require_admin, require_joined
from shared.settings import CONF, FORWARD_DELAY
from telegram import Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

MAIN_CHANNEL = CONF['CHANNEL']
STATE = {
    'FA': {},
    'SCL': {}
}


@require_joined
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if user.id in CONF['ADMINS']:
        await update.message.reply_text(
            'list of all channels',
            reply_markup=await get_keyboard_chats(ctx.bot)
        )
    else:
        await update.message.reply_text(
            'خوش آمدید، برای ارسال بنر در کانال بنر خود را فوروارد کنید.',
        )


@require_admin
async def send_all(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    STATE['FA'][user.id] = not STATE['FA'].get(user.id, False)

    if STATE['FA'][user.id]:
        await update.message.reply_text((
            'پیامت رو ارسال کن \n'
            'غیرفعال کردن با /send_all'
        ))
    else:
        await update.message.reply_text(
            'ارسال همگانی غیرفعال شد.'
        )


async def send_all_job(ctx: ContextTypes.DEFAULT_TYPE):
    users = get_users().copy()
    data = {
        'success': 0,
        'blocked': 0,
        'error': 0,
        'timeout': 0,
    }

    for uid, udata in users.items():
        sleep(0.2)
        uid = int(uid)
        try:
            chat = await ctx.bot.get_chat(uid)
            if chat.type != 'private':
                return

            await ctx.bot.forward_message(
                uid,
                from_chat_id=ctx.job.chat_id,
                message_id=ctx.job.data,
            )
            data['success'] += 1
        except RetryAfter as e:
            sleep(e.retry_after + 10)
            logging.info(f'[send_all]: retry_after {e.retry_after}')
            data['timeout'] += 1
        except Forbidden:
            username = None
            if isinstance(udata, dict):
                username = udata['username']

            if username is None:
                user_remove(uid)

            logging.info(f'[send_all]: forbidden {uid} - {username}')
            data['blocked'] += 1
        except NetworkError:
            data['error'] += 1
        except TelegramError as e:
            logging.exception(e)
            data['error'] += 1

    sleep(2)
    await ctx.bot.send_message(ctx.job.user_id, (
        'send to all done.\n'
        f'success: {data["success"]}\n'
        f'blocked: {data["blocked"]}\n'
        f'error: {data["error"]}\n'
        f'timeout: {data["timeout"]}\n'
    ))


async def forward_to_channel_job(ctx: ContextTypes.DEFAULT_TYPE):
    await ctx.bot.forward_message(
        MAIN_CHANNEL,
        from_chat_id=ctx.job.chat_id,
        message_id=ctx.job.data,
    )


@ require_joined
async def send_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total_users = len(get_users())
    msg = update.message
    user = msg.from_user

    if (
        not msg.forward_from_chat or
        msg.forward_from_chat.type != 'channel'
    ):
        return

    if STATE['FA'].pop(user.id, False):
        ctx.job_queue.run_once(
            send_all_job, 1,
            chat_id=msg.chat.id,
            user_id=user.id,
            data=msg.message_id,
            name='send_all'
        )
        await msg.reply_text(
            f'✅ پیام شما ذخیره شد ، پیام شما به {total_users} نفر ارسال خواهد شد .'
        )
        return

    if not is_forwards_enable():
        await msg.reply_text(
            ('فعلا ربات خاموشه وقتی اومدم فور میزنم تا اون موقع میتونی از'
             ' گروه جفج دیدن کنی @joinforjoindaily')
        )
        return

    exp = check_user(user)

    h = exp // 3600
    m = exp % 3600 // 60
    s = exp % 3600 % 60

    if exp:
        await msg.reply_text(
            (f'شما به تازگی پیام ارسال کردید برای ارسال'
             f' مجدد پیام باید {h}:{m}:{s} صبر کنید.')
        )
        return

    ctx.job_queue.run_once(
        forward_to_channel_job, FORWARD_DELAY,
        chat_id=msg.chat.id,
        user_id=user.id,
        data=msg.message_id,
    )

    await msg.reply_text((
        'پست شما با موفقیت برای ادمین ارسال شد در صورت تایید'
        ' ،در چنل گذاشته میشود.\n\n'
        'مطمعن شوید پست زیر رو به چنلتون فور زدید\n'
        'https://t.me/daily_gostardeh/95'
    ))

    # await msg.forward(MAIN_CHANNEL)


@require_admin
async def set_chat_limit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    cid = STATE['SCL'].pop(user.id, 0)
    if not cid:
        return

    limit = int(update.message.text)
    channel_set_limit(cid, limit)
    await update.message.reply_text(
        'done. use /start\nset the limit to -1 for disabling it'
    )


async def query_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data or not query.message:
        return

    data = query.data.split('#')

    if len(data) != 2:
        return

    action, cid = data
    cid = int(cid)

    if action == 'toggle_chat':
        channel_toggle(cid)
    elif action == 'leave_chat':
        if (await ctx.bot.leave_chat(cid)):
            channel_remove(cid)
    elif action == 'toggle_forwards':
        toggle_forwards()
    elif action == 'set_chat_limit':
        STATE['SCL'][query.from_user.id] = cid
        await ctx.bot.send_message(
            query.from_user.id,
            'ok. now send a number ...'
        )
        return
    else:
        return

    await query.edit_message_reply_markup(await get_keyboard_chats(ctx.bot))


def main(args: list[str]):
    logging.info('Starting Athena')
    setup_databases()

    application = Application.builder().token(CONF['TOKEN']).build()
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('users', users))
    application.add_handler(CommandHandler('send_all', send_all))

    application.add_handler(ChatMemberHandler(
        chat_member_update, ChatMemberHandler.CHAT_MEMBER
    ))
    application.add_handler(ChatMemberHandler(
        my_chat_update, ChatMemberHandler.MY_CHAT_MEMBER
    ))

    application.add_handler(CallbackQueryHandler(query_update))
    application.add_handler(MessageHandler(
        ((filters.TEXT | filters.PHOTO) &
         (filters.FORWARDED & filters.ChatType.PRIVATE)),
        send_message
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex(r'^-?\d+$') & filters.ChatType.PRIVATE,
        set_chat_limit
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main(sys.argv)
