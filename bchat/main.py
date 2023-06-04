
import logging

from database import get_user, update_user
from deps import require_user_data
from models import GENDER_DISPLAY, UserModel
from modules.admin import HANDLERS_ADMIN
from modules.channels import HANDLERS_CHANNELS
from modules.direct import HANDLERS_DIRECT
from modules.user import HANDLERS_USER
from settings import DEF_PHOTO, HOME_DIR, MAIN_KEYBOARD, database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes
from utils import config

from gshare import get_error_handler, setup_logging

# from telegram.error import Forbidden, NetworkError, RetryAfter, TelegramError
# from telegram.ext import ChatMemberHandler


setup_logging(HOME_DIR)


Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def start(update: Update, ctx: Ctx, user_data: UserModel):
    if ctx.args:
        codename = ctx.args[0]
        logging.info(f'user started with a code {codename}')

        if codename == user_data.codename:
            await update.effective_message.reply_text(
                'اینکه آدم گاهی با خودش حرف بزنه خوبه ، '
                'ولی اینجا نمیتونی به خودت پیام ناشناس بفرستی ! :)\n\n'
                'چه کاری برات انجام بدم؟'
            )
            return

        code_user_data = await get_user(codename=codename)
        if code_user_data is None:
            await update.effective_message.reply_text(
                f'کاربری با کد {codename} پیدا نشد. ❌'
            )
            return

        if user_data.new_user:
            await update_user(
                code_user_data.user_id,
                total_score=code_user_data.total_score + 1
            )

        text = (
            f'نام: {code_user_data.name}\n'
            f'جنسیت: {GENDER_DISPLAY[code_user_data.gender]}\n'
            f'سن: {user_data.age}\n'
        )

        trail_text = '\n\n👇 دکمه ارسال پیام رو بزن و بعدش پیامت رو ارسال کن.'

        keyboard = []
        if str(code_user_data.user_id) in user_data.saved_list:
            keyboard.append(InlineKeyboardButton(
                'حذف کاربر ❌',
                callback_data=(
                    f'remove_saved_user#{code_user_data.user_id}'
                )
            ))
        else:
            if len(user_data.saved_list.keys()) < 10:
                keyboard.append(InlineKeyboardButton(
                    'ذخیر کاربر ⭐',
                    callback_data=(
                        f'save_user#{code_user_data.user_id}'
                    )
                ))

        if str(user_data.user_id) not in code_user_data.block_list:
            keyboard.append(InlineKeyboardButton(
                'ارسال پیام ✉',
                callback_data=(
                    f'send_direct_message#{code_user_data.user_id}'
                )
            ))
        else:
            trail_text = (
                '\n\nاین کاربر شما را بلاک کرده. ⛔'
            )

        # pictures = await ctx.bot.get_user_profile_photos(
        #     code_user_data.user_id, limit=1
        # )

        file_id = DEF_PHOTO
        # if pictures.total_count > 0:
        #     file_id = pictures.photos[0][0].file_id

        await update.effective_message.reply_photo(
            file_id, text + trail_text,
            reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
        )

        return

    await update.effective_message.reply_text(
        f'سلام {user_data.name}\n\n'
        'چه کاری برات انجام بدم؟',
        reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD)
    )


@require_user_data
async def coming_soon(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer('به زوردی... 🌩')
    # await update.effective_message.reply_text()


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

    for handler in [
        *HANDLERS_DIRECT, *HANDLERS_ADMIN,
        *HANDLERS_CHANNELS, *HANDLERS_USER
    ]:
        application.add_handler(handler)

    application.add_handler(CallbackQueryHandler(
        coming_soon,
        pattern='^coming_soon$',
        block=False
    ))

    # send message

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
