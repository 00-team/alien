

import logging

from db.user import user_get, user_update
from deps import require_user_data
from models import GENDER_DISPLAY, UserModel, UserTable
from settings import MAIN_KEYBOARD
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils import config

Ctx = ContextTypes.DEFAULT_TYPE


@require_user_data
async def start(update: Update, ctx: Ctx, state: UserModel):
    if ctx.args:
        codename = ctx.args[0]
        logging.info(f'user started with a code {codename}')

        if codename == state.codename:
            await update.effective_message.reply_text(
                'اینکه آدم گاهی با خودش حرف بزنه خوبه ، '
                'ولی اینجا نمیتونی به خودت پیام ناشناس بفرستی ! :)\n\n'
                'چه کاری برات انجام بدم؟'
            )
            return

        target = await user_get(
            UserTable.codename == codename
        )
        if target is None:
            await update.effective_message.reply_text(
                f'کاربری با کد {codename} پیدا نشد. ❌'
            )
            return

        if state.new_user:
            await user_update(
                UserTable.user_id == target.user_id,
                total_score=target.total_score + 1
            )
            await user_update(
                UserTable.user_id == state.user_id,
                parent=target.user_id
            )

        text = (
            f'نام: {target.name}\n'
            f'جنسیت: {GENDER_DISPLAY[target.gender]}\n'
            f'سن: {target.age}\n'
        )

        trail_text = '\n\n👇 دکمه ارسال پیام رو بزن و بعدش پیامت رو ارسال کن.'

        keyboard = []
        if str(target.user_id) in state.saved_list:
            keyboard.append(InlineKeyboardButton(
                'حذف کاربر ❌',
                callback_data=(
                    f'remove_saved_user#{target.user_id}'
                )
            ))
        else:
            if len(state.saved_list.keys()) < 10:
                keyboard.append(InlineKeyboardButton(
                    'ذخیر کاربر ⭐',
                    callback_data=(
                        f'save_user#{target.user_id}'
                    )
                ))

        if str(state.user_id) not in target.block_list:
            keyboard.append(InlineKeyboardButton(
                'ارسال پیام ✉',
                callback_data=(
                    f'send_direct_message#{target.user_id}'
                )
            ))
        else:
            trail_text = (
                '\n\nاین کاربر شما را بلاک کرده. ⛔'
            )

        # pictures = await ctx.bot.get_user_profile_photos(
        #     code_user_data.user_id, limit=1
        # )

        file_id = config['default_profile_picture']
        if target.picture:
            file_id = target.picture

        # if pictures.total_count > 0:
        #     file_id = pictures.photos[0][0].file_id

        await update.effective_message.reply_photo(
            file_id, text + trail_text,
            reply_markup=InlineKeyboardMarkup([keyboard]) if keyboard else None
        )

        return

    await update.effective_message.reply_text(
        f'سلام {state.name}\n\n'
        'چه کاری برات انجام بدم؟',
        reply_markup=ReplyKeyboardMarkup(MAIN_KEYBOARD)
    )
