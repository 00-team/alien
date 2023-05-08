

import logging

from dependencies import require_user_data
from models import GENDER_DISPLAY, Genders, UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import config, toggle_code

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
                'Edit Gender', callback_data='user_edit_gender'
            ),
            InlineKeyboardButton(
                'Edit Age', callback_data='user_edit_age'
            ),
        ]])
    )


@require_user_data
async def user_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    await update.message.reply_text(
        'choice which one do you want to edit',
        reply_markup=ReplyKeyboardMarkup(
            [['gender', 'age']],
            # one_time_keyboard=True,
            # input_field_placeholder='GFG'
        )
    )

    return 'CHANGE_ROUTE'


@require_user_data
async def user_edit_gender(update: Update, ctx: Ctx, user_data: UserModel):
    logging.info('in user edit gender')
    keyboard = []

    for g in Genders.__members__.values():
        if g.value == user_data.gender:
            continue

        keyboard.append([InlineKeyboardButton(
            GENDER_DISPLAY[g],
            callback_data=f'user_gender_{g.value}'
        )])

    keyboard.append([InlineKeyboardButton(
        'Cancel ❌', callback_data='cancel_edit_profile'
    )])

    await update.effective_message.edit_reply_markup(
        InlineKeyboardMarkup(keyboard)
    )

    return 'EDIT_GENDER'


@require_user_data
async def user_set_gender(update: Update, ctx: Ctx, user_data: UserModel):
    logging.info(update.callback_query.data)

    await update.effective_message.reply_text(
        'your chosen gender: ' + update.callback_query.data
    )

    return ConversationHandler.END


@require_user_data
async def user_edit_age(update: Update, ctx: Ctx, user_data: UserModel):

    await update.message.reply_text(
        'send your age btween 10 and 80',

    )

    return 'EDIT_AGE'


@require_user_data
async def cancel_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    # user = update.message.from_user
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        # reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
