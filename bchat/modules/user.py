

from database import get_user, update_user
from dependencies import require_user_data
from models import GENDER_DISPLAY, Genders, UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import config, toggle_code

Ctx = ContextTypes.DEFAULT_TYPE
profile_keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        'Edit Gender', callback_data='user_edit_gender'
    ),
    InlineKeyboardButton(
        'Edit Age', callback_data='user_edit_age'
    ),
]])


def get_link(row_id, bot_username):
    return f't.me/{bot_username}?start={toggle_code(row_id)}'


def get_profile_text(user_data: UserModel, bot_username):
    return (
        f'name: {user_data.name}\n'
        f'gender: {GENDER_DISPLAY[user_data.gender]}\n'
        f'age: {user_data.age}\n\n'
        f'link: {get_link(user_data.row_id, bot_username)}\n\n'
    )


@require_user_data
async def user_link(update: Update, ctx: Ctx, user_data: UserModel):
    await update.message.reply_text(
        'your link\n' + get_link(user_data.row_id, ctx.bot.username)
    )


@require_user_data
async def user_profile(update: Update, ctx: Ctx, user_data: UserModel):
    user = update.effective_user
    pictures = await user.get_profile_photos(limit=1)

    file_id = config['default_profile_picture']

    if pictures.total_count > 0:
        file_id = pictures.photos[0][0].file_id

    await update.message.reply_photo(
        file_id, get_profile_text(user_data, ctx.bot.username),
        reply_markup=profile_keyboard
    )


@require_user_data
async def user_edit_gender(update: Update, ctx: Ctx, user_data: UserModel):
    keyboard = []

    for g in Genders.__members__.values():
        if g.value == user_data.gender:
            continue

        keyboard.append([InlineKeyboardButton(
            GENDER_DISPLAY[g],
            callback_data=f'user_gender_{g.value}'
        )])

    keyboard.append([InlineKeyboardButton(
        'لغو ❌', callback_data='cancel_edit_profile'
    )])

    await update.effective_message.edit_reply_markup(
        InlineKeyboardMarkup(keyboard)
    )

    return 'EDIT_GENDER'


@require_user_data
async def user_set_gender(update: Update, ctx: Ctx, user_data: UserModel):
    gender = int(update.callback_query.data[12:])

    await update_user(user_data.user_id, gender=gender)
    user_data.gender = gender

    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        reply_markup=profile_keyboard
    )

    return ConversationHandler.END


@require_user_data
async def user_edit_age(update: Update, ctx: Ctx, user_data: UserModel):

    await update.effective_message.edit_caption(
        'سن خود را وارد کنید. \nبین ۵ تا ۹۹ سال.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_edit_profile'
        )]])
    )

    ctx.user_data['user_edit_age_message_id'] = update.effective_message.id

    return 'EDIT_AGE'


@require_user_data
async def user_set_age(update: Update, ctx: Ctx, user_data: UserModel):
    error_msg_id = ctx.user_data.get('user_set_age_error_message_id')

    try:
        age = int(update.effective_message.text)
        if age < 5 or age > 99:
            raise ValueError('invalid age rage')
    except Exception:
        await update.effective_message.delete()

        if error_msg_id is None:
            em = await update.effective_message.reply_text(
                'خطا! پیام باید یک عدد بین ۵ تا ۹۹ باشد. ❌'
            )
            ctx.user_data['user_set_age_error_message_id'] = em.id

        return

    msg_id = ctx.user_data.pop('user_edit_age_message_id', None)

    await update_user(user_data.user_id, age=age)
    user_data.age = age
    chat_id = update.effective_message.chat_id

    if msg_id:
        await ctx.bot.edit_message_caption(
            chat_id,
            message_id=msg_id,
            caption=get_profile_text(user_data, ctx.bot.username),
            reply_markup=profile_keyboard
        )
        await update.effective_message.delete()
    else:
        await update.effective_message.reply_text('سن شما ثبت شد. ✅')

    if error_msg_id:
        await ctx.bot.delete_message(chat_id, error_msg_id)

    return ConversationHandler.END


@require_user_data
async def cancel_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        reply_markup=profile_keyboard
    )

    return ConversationHandler.END
