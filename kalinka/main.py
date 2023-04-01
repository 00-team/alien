

import logging

from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import MessageHandler, filters

from modules.admin import error_handler
from modules.bot import bot_start
from modules.twitter import cancel, menu, query_update, update_message
from shared.database import setup_databases
from shared.settings import TOKEN

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import , ChatMemberHandler


def main():
    logging.info('Starting Kalinka')
    setup_databases()

    application = Application.builder().token(TOKEN).build()
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler(['help', 'start', 'menu'], menu))
    application.add_handler(CommandHandler('cancel', cancel))

    application.add_handler(CallbackQueryHandler(query_update))
    application.add_handler(MessageHandler(
        (filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE),
        update_message)
    )

    bot_start()

    application.run_polling(
        # allowed_updates=Update.ALL_TYPES
    )


if __name__ == '__main__':
    main()
