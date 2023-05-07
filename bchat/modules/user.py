

from dependencies import require_user_data
from models import GENDER_DISPLAY, UserModel
from settings import config
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils import toggle_code

Ctx = ContextTypes.DEFAULT_TYPE


def get_link(code):
    bot_username = config['BOT']['username']
    return f't.me/{bot_username}?start={code}'


@require_user_data
async def user_link(update: Update, ctx: Ctx, user_data: UserModel):
    code = toggle_code(user_data.row_id)
    await update.message.reply_text('your link\n' + get_link(code))


@require_user_data
async def user_profile(update: Update, ctx: Ctx, user_data: UserModel):
    code = toggle_code(user_data.row_id)
    user = update.effective_user
    pictures = await user.get_profile_photos(limit=1)

    file_id = config['default_profile_picture']

    if pictures.total_count > 0:
        file_id = pictures.photos[0][0].file_id

    await update.message.reply_photo(
        file_id,
        (
            f'name: {user_data.name}\n'
            f'gender: {GENDER_DISPLAY[user_data.gender]}\n'
            f'age: {user_data.age}\n\n'
            f'link: {get_link(code)}\n\n'
        ),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'Edit Profile', callback_data='edit_profile'
            )
        ]])
    )


# @require_user_data
# async def user_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
#     await update.message.
#     return ''
