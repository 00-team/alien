

import logging

from dependencies import require_user_data
from models import GENDER_DISPLAY, UserModel
from settings import config
from telegram import Update
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
async def user_info(update: Update, ctx: Ctx, user_data: UserModel):
    code = toggle_code(user_data.row_id)

    await update.message.reply_text(
        f'your name: {user_data.name}'
        f'your link: {get_link(code)}'
        f'your gender: {GENDER_DISPLAY[user_data.gender]}'
    )


@require_user_data
async def user_profile(update: Update, ctx: Ctx, user_data: UserModel):
    user = update.effective_user
    pictures = await user.get_profile_photos(limit=1)

    logging.info(
        f'{pictures.total_count}'
    )

    logging.info(pictures)

    await update.message.reply_photo(pictures.photos[0][0].file_id, 'GG')
