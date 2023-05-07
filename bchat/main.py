
import logging

from database import add_user, get_user
from modules import user_info, user_link
from settings import HOME_DIR, config, database
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from gshare import get_error_handler, setup_logging

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

    user_data = await get_user(user_id=user.id)
    if user_data is None:
        res = await add_user(user.id, user.full_name)
        logging.info(f'res: {res}')

    logging.info(user_data)


async def post_init(self):
    await database.connect()
    bot = await self.bot.get_me()

    config['BOT'] = {
        'username': bot.username,
        'name': bot.full_name,
        'id': bot.id
    }

    logging.info('Starting Bchat')


async def post_shutdown(self):
    await database.disconnect()
    logging.info('Shuting Down Bchat')


def main():

    application = Application.builder().token(config['TOKEN']).build()
    application.add_error_handler(get_error_handler(config['ADMINS'][0]))

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('my_link', user_link))
    application.add_handler(CommandHandler('my_info', user_info))
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
    main()
