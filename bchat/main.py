
import logging

from deps import require_user_data
from models import UserModel
from modules.admin import HANDLERS_ADMIN
from modules.channels import HANDLERS_CHANNELS
from modules.direct import HANDLERS_DIRECT
from modules.shop import HANDLERS_SHOP
from modules.start import start
from modules.user import HANDLERS_USER
from settings import HOME_DIR, sqlx
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes
from utils import config

from gshare import get_error_handler, setup_logging

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import ChatMemberHandler


setup_logging(HOME_DIR)


Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def coming_soon(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer('به زوردی... 🌩')


async def post_init(self):
    await sqlx.connect()
    logging.info('Starting Bchat')


async def post_shutdown(self):
    await sqlx.disconnect()
    logging.info('Shuting Down Bchat')


def main():

    application = Application.builder().token(config['TOKEN']).build()
    application.add_error_handler(get_error_handler(config['ADMINS'][0]))

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # application.add_handler(MessageHandler(
    #     filters.VIDEO | filters.PHOTO | filters.ANIMATION,
    #     get_file_id
    # ))

    application.add_handler(CommandHandler(['start', 'restart'], start))

    for handler in [
        *HANDLERS_DIRECT, *HANDLERS_ADMIN,
        *HANDLERS_CHANNELS, *HANDLERS_USER,
        *HANDLERS_SHOP
    ]:
        application.add_handler(handler)

    application.add_handler(CallbackQueryHandler(
        coming_soon,
        pattern='^coming_soon$',
        block=False
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
