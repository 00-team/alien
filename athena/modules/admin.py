
import html
import json
import logging
import traceback
from io import StringIO

from shared.database import get_users
from shared.dependencies import require_admin
from shared.settings import BLOCKED_CHANNELS_PATH, BLOCKED_USERS_PATH
from shared.settings import CHANNEL_DB_PATH, CONF, GENERAL_DB_PATH
from shared.settings import USER_DB_PATH
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import Forbidden, NetworkError
from telegram.ext import ContextTypes


@require_admin
async def help_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text((
        '/backup -> get backup\n\n'
        '/users -> get all the usernames\n'
        '/start -> get list of channels\n'
        '/send_all -> send a message to all users\n'
        '/block <user_id?> -> get a list of blocked users or block a user\n'
        '/block_channel <channel_id?> -> '
        'get a list of blocked channels or block a channel\n'
        '/help -> for getting the message\n'
        '🐧'
    ))


MAX_FILE_SIZE = 50 * 1024 * 1024


@require_admin
async def backup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    for p in [
        USER_DB_PATH, CHANNEL_DB_PATH, GENERAL_DB_PATH,
        BLOCKED_USERS_PATH, BLOCKED_CHANNELS_PATH
    ]:
        if p.stat().st_size >= MAX_FILE_SIZE:
            await msg.reply_text(f'{p.name} is too big ❌')
            continue

        await msg.reply_document(p, caption=p.name)
        logging.info(f'a backup for {p.name} was made')


@require_admin
async def users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    users = get_users().values()

    text = StringIO()
    size = text.write(f'user count: {len(users)} 🐧\n')
    usernames = 0

    for data in users:
        if isinstance(data, int) or not data['username']:
            continue

        username = data['username']
        add_size = len(username) + 2
        usernames += 1

        if size + add_size > 4000:
            await msg.reply_text(text.getvalue())
            text.seek(0)
            text.truncate()
            size = text.write(f'{len(users)} 🐧\n@{username} ')
        else:
            text.write(f'@{username} ')
            size += add_size

    await msg.reply_text(text.getvalue())
    await msg.reply_text(
        f'total user: {len(users)}\ntotal usernames: {usernames}'
    )


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        if isinstance(ctx.error, NetworkError):
            logging.error((
                'a network error has occurred.\n' +
                ctx.error.message
            ))
            return

        if isinstance(ctx.error, Forbidden):
            logging.warn(('a Forbidden has happened.\n' + ctx.error.message))
            return

        logging.error(
            msg='Exception while handling an update:',
            exc_info=ctx.error
        )

        tb_list = traceback.format_exception(
            None, ctx.error, ctx.error.__traceback__
        )
        tb_string = ''.join(tb_list)

        if isinstance(update, Update):
            update_str = json.dumps(
                update.to_dict(), indent=2, ensure_ascii=False)
        else:
            update_str = str(update)

        message = (
            f'An exception was raised while handling an update\n\n'
            f'<pre>{html.escape(update_str)}</pre>\n\n'
            f'<pre>ctx.chat_data = {html.escape(str(ctx.chat_data))}</pre>\n\n'
            f'<pre>ctx.user_data = {html.escape(str(ctx.user_data))}</pre>\n\n'
            f'<pre>{html.escape(tb_string)}</pre>'
        )

        DEV = CONF['ADMINS'][0]

        await ctx.bot.send_message(
            chat_id=DEV, text=message, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.exception(e)
