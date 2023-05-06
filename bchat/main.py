
import logging
import sys
from pathlib import Path

from telegram import Update
from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from gshare import DbDict, get_error_handler, setup_logging

HOME_DIR = Path(__file__).parent

setup_logging(HOME_DIR)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(f'hi there {user.id}')


def main(args: list[str]):
    logging.info('Starting Bchat')
    config = DbDict(args[1], load=True)

    application = Application.builder().token(config['TOKEN']).build()
    application.add_error_handler(get_error_handler(config['ADMINS'][0]))

    application.add_handler(CommandHandler('start', start))
    # application.add_handler(CommandHandler('help', help_command))
    # application.add_handler(CommandHandler('users', users))
    # application.add_handler(CommandHandler('send_all', send_all))
    # application.add_handler(CommandHandler('block', block))
    #
    # application.add_handler(ChatMemberHandler(
    #     chat_member_update, ChatMemberHandler.CHAT_MEMBER
    # ))
    # application.add_handler(ChatMemberHandler(
    #     my_chat_update, ChatMemberHandler.MY_CHAT_MEMBER
    # ))
    #
    # application.add_handler(CallbackQueryHandler(query_update))
    # application.add_handler(MessageHandler(
    #     ((filters.TEXT | filters.PHOTO) &
    #      (filters.FORWARDED & filters.ChatType.PRIVATE)),
    #     send_message
    # ))
    # application.add_handler(MessageHandler(
    #     filters.TEXT & filters.Regex(r'^-?\d+$') & filters.ChatType.PRIVATE,
    #     set_chat_limit
    # ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main(sys.argv)
