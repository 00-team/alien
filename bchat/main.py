
import logging

from database import get_user
from dependencies import require_user_data
from models import UserModel
from models.user import GENDER_DISPLAY, gender_pattern
from modules import cancel_direct_message, cancel_edit_profile
from modules import handle_direct_message, send_direct_message
from modules import send_not_seen_messages, show_direct_message
from modules import show_saved_users, toggle_saved_user, toggle_user_block
from modules import user_edit_age, user_edit_gender, user_edit_name, user_link
from modules import user_link_extra, user_profile, user_set_age
from modules import user_set_gender, user_set_name
from settings import DEF_PHOTO, HOME_DIR, KW_DRTNSEN, KW_MY_LINK, KW_PROFILE
from settings import KW_SAVELST, MAIN_KEYBOARD, database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
from telegram.ext import filters
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

        pictures = await ctx.bot.get_user_profile_photos(
            code_user_data.user_id, limit=1
        )

        file_id = DEF_PHOTO
        if pictures.total_count > 0:
            file_id = pictures.photos[0][0].file_id

        res = await update.effective_message.reply_photo(
            file_id, text + trail_text,
            reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
        )
        logging.info(res)

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

    application.add_handler(MessageHandler(
        filters.Text([KW_PROFILE]),
        user_profile
    ))

    application.add_handler(MessageHandler(
        filters.Text([KW_MY_LINK]),
        user_link
    ))

    application.add_handler(MessageHandler(
        filters.Text([KW_DRTNSEN]),
        send_not_seen_messages
    ))

    application.add_handler(CallbackQueryHandler(
        show_direct_message,
        pattern='^show_direct#[0-9]+$'
    ))

    application.add_handler(CallbackQueryHandler(
        toggle_saved_user,
        pattern='^(remove_saved_user|save_user)#[0-9]+$'
    ))

    application.add_handler(MessageHandler(
        filters.Text([KW_SAVELST]),
        show_saved_users,
    ))

    application.add_handler(CallbackQueryHandler(
        send_not_seen_messages,
        pattern='^show_direct#all$'
    ))

    application.add_handler(CallbackQueryHandler(
        toggle_user_block,
        pattern='^toggle_user_block#[0-9]+$'
    ))

    application.add_handler(CallbackQueryHandler(
        user_link_extra,
        pattern='^user_link_(.*)$'
    ))

    application.add_handler(CallbackQueryHandler(
        coming_soon,
        pattern='^coming_soon$'
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

    # send message
    application.add_handler(ConversationHandler(
        per_message=False,
        entry_points=[
            CallbackQueryHandler(
                send_direct_message,
                pattern='^(send_direct_message|direct_reply)#(.*)$'
            )
        ],
        states={
            'GET_MESSAGE': [
                MessageHandler(
                    filters.ChatType.PRIVATE,
                    handle_direct_message,
                )
            ],
        },
        fallbacks=[
            CallbackQueryHandler(
                cancel_direct_message,
                pattern='^cancel_direct_message$'
            )
        ],
    ))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
