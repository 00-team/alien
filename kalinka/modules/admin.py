
import html
import json
import logging
import traceback

from shared.settings import ADMINS
from telegram import Update
from telegram.constants import ParseMode
from telegram.error import NetworkError
from telegram.ext import ContextTypes


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        if isinstance(ctx.error, NetworkError):
            logging.error((
                'a network error has occurred.\n' +
                ctx.error.message
            ))
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

        await ctx.bot.send_message(
            chat_id=ADMINS[0], text=message, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logging.exception(e)
