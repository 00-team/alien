
import logging

from database import get_user
from dependencies import require_user_data
from models import UserModel
from models.user import gender_pattern
from modules import cancel_edit_profile, get_file_id, get_profile_text
from modules import user_edit_age, user_edit_gender, user_edit_name, user_link
from modules import user_link_extra, user_profile, user_set_age
from modules import user_set_gender, user_set_name
from settings import HOME_DIR, KW_MY_LINK, KW_PROFILE, MAIN_KEYBOARD, database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters
from utils import config, toggle_code

from gshare import get_error_handler, setup_logging

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import ChatMemberHandler


setup_logging(HOME_DIR)


Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def start(update: Update, ctx: Ctx, user_data: UserModel):
    if ctx.args:
        code = ctx.args[0]
        logging.info(f'user started with a code {code}')
        code_row_id = toggle_code(code)
        if code_row_id == user_data.row_id:
            await update.effective_message.reply_text(
                'اینکه آدم گاهی با خودش حرف بزنه خوبه ، '
                'ولی اینجا نمیتونی به خودت پیام ناشناس بفرستی ! :)\n\n'
                'چه کاری برات انجام بدم؟'
            )
            return

        code_user_data = await get_user(row_id=code_row_id)
        if code_user_data is None:
            await update.effective_message.reply_text(
                f'کاربری با کد {code} پیدا نشد. ❌'
            )
            return

        pictures = await ctx.bot.get_user_profile_photos(
            code_user_data.user_id, limit=1
        )

        file_id = config['default_profile_picture']
        if pictures.total_count > 0:
            file_id = pictures.photos[0][0].file_id

        text = get_profile_text(code_user_data, ctx.bot.username)

        text += (
            f'\n\n می تونی برای {code_user_data.name} پیام ناشناس بفرستی'
            ' و هر حرف یا انتقادی که تو دلت هست رو بگی چون پیامت به صورت '
            'کاملا ناشناس ارسال میشه!\n'
        )

        await update.effective_message.reply_photo(
            file_id, text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    'ارسال پیام ✉',
                    callback_data=f'send_user_message_{code_user_data.user_id}'
                )
            ]])
        )

        return

    await update.effective_message.reply_text(
        f'سلام {user_data.name}\n\n'
        'چه کاری برات انجام بدم؟',
        reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD)
    )


async def post_init(self):
    await database.connect()
    logging.info('Starting Bchat')


async def post_shutdown(self):
    await database.disconnect()
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

    application.add_handler(MessageHandler(
        filters.Text([KW_PROFILE]),
        user_profile
    ))

    application.add_handler(MessageHandler(
        filters.Text([KW_MY_LINK]),
        user_link
    ))

    application.add_handler(CallbackQueryHandler(
        user_link_extra,
        pattern='^user_link_(.*)$'
    ))

    # edit gender
    application.add_handler(ConversationHandler(
        per_message=True,
        entry_points=[
            CallbackQueryHandler(
                user_edit_gender,
                pattern='^user_edit_gender$'
            ),
        ],
        states={
            'EDIT_GENDER': [CallbackQueryHandler(
                user_set_gender,
                pattern=f'^user_gender_({gender_pattern})$'
            )],
        },
        fallbacks=[
            CallbackQueryHandler(
                cancel_edit_profile,
                pattern='^cancel_edit_profile$'
            )
        ],
    ))

    # edit age
    application.add_handler(ConversationHandler(
        per_message=False,
        entry_points=[
            CallbackQueryHandler(
                user_edit_age,
                pattern='^user_edit_age$'
            )
        ],
        states={
            'EDIT_AGE': [
                MessageHandler(
                    filters.ChatType.PRIVATE,
                    user_set_age,
                )
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                cancel_edit_profile,
                pattern='^cancel_edit_profile$'
            )
        ],
    ))

    # edit name
    application.add_handler(ConversationHandler(
        per_message=False,
        entry_points=[
            CallbackQueryHandler(
                user_edit_name,
                pattern='^user_edit_name$'
            )
        ],
        states={
            'EDIT_NAME': [
                MessageHandler(
                    filters.ChatType.PRIVATE,
                    user_set_name,
                )
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                cancel_edit_profile,
                pattern='^cancel_edit_profile$'
            )
        ],
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
