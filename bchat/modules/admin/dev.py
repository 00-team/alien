
import logging

from deps import require_admin
from settings import DATABASE_PATH
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


MAX_FILE_SIZE = 50 * 1024 * 1024


@require_admin
async def backup(update: Update, ctx: Ctx):
    msg = update.effective_message

    if DATABASE_PATH.stat().st_size < 50 * 1024 * 10:
        await msg.reply_document(DATABASE_PATH, caption='main db')
        logging.info('a backup was made')
    else:
        await msg.reply_text('main db is too big ❌')


H_DEV = [
    CommandHandler(['backup'], backup)
]
