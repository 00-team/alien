
import logging
import sys

from database import add_user, database, get_user
from settings import HOME_DIR
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from gshare import DbDict, get_error_handler, setup_logging

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import CallbackQueryHandler, ChatMemberHandler
# from telegram.ext import essageHandler, filters


setup_logging(HOME_DIR)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    keyboard = [
        [KeyboardButton('row 1 text 1')],
        [KeyboardButton('row 2 text 2')],
    ]
    await update.message.reply_text(
        f'hi there {user.id}',
        reply_markup=ReplyKeyboardMarkup(keyboard)
    )

    logging.info(ctx.args)

    logging.info(get_user(user_id=user.id))

    # database.execute()

    # user.full_name


async def post_init():
    await database.connect()
    logging.info('Starting Bchat')


async def post_shutdown():
    await database.disconnect()
    logging.info('Shuting Down Bchat')


def main(args: list[str]):
    config = DbDict(args[1], load=True)

    application = Application.builder().token(config['TOKEN']).build()
    application.add_error_handler(get_error_handler(config['ADMINS'][0]))

    application.post_init = post_init
    application.post_shutdown = post_shutdown

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
