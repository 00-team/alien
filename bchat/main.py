
import logging

from database import add_user, get_user
from models.user import gender_pattern
from modules import cancel_edit_profile, user_edit_age, user_edit_gender
from modules import user_edit_profile, user_link, user_profile
from modules import user_set_gender
from settings import HOME_DIR, database
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters
from utils import config

from gshare import get_error_handler, setup_logging

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import ChatMemberHandler


setup_logging(HOME_DIR)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [KeyboardButton('profile')],
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
    application.add_handler(CommandHandler('my_profile', user_profile))

    application.add_handler(MessageHandler(
        filters.Text(['profile']),
        user_profile
    ))

    def x(d):
        logging.info(d)
        return True

    application.add_handler(ConversationHandler(
        per_message=True,
        entry_points=[CallbackQueryHandler(
            user_edit_gender,
            pattern=x
        )],
        states={
            'EDIT_GENDER': [CallbackQueryHandler(
                user_set_gender,
                pattern=f'^user_gender_({gender_pattern})$'
            )]
        },
        fallbacks=[CallbackQueryHandler(
            cancel_edit_profile, pattern='^cancel_edit_profile$')],
        # conversation_timeout=60
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
