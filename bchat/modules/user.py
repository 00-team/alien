

import json
import logging

from database import update_user
from dependencies import require_user_data
from models import GENDER_DISPLAY, Genders, UserModel
from settings import AGE_RANGE, NAME_RANGE
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import config, toggle_code

Ctx = ContextTypes.DEFAULT_TYPE
profile_keyboard = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        'تغییر جنسیت', callback_data='user_edit_gender'
    ),
    InlineKeyboardButton(
        'تغییر سن', callback_data='user_edit_age'
    ),
    InlineKeyboardButton(
        'تغییر نام', callback_data='user_edit_name'
    ),
]])


def get_link(row_id, bot_username):
    return f't.me/{bot_username}?start={toggle_code(row_id)}'


def get_profile_text(user_data: UserModel, bot_username):
    return (
        f'نام: {user_data.name}\n'
        f'جنسیت: {GENDER_DISPLAY[user_data.gender]}\n'
        f'سن: {user_data.age}\n\n'
        f'لینک ناشناس: {get_link(user_data.row_id, bot_username)}\n\n'
    )


@require_user_data
async def user_link(update: Update, ctx: Ctx, user_data: UserModel):
    link = get_link(user_data.row_id, ctx.bot.username)

    await update.effective_message.reply_text(
        f'سلام {user_data.name} هستم ✋😉\n\n'
        f'👇👇\n{link}'
    )

    await update.effective_message.reply_text((
        '👆👆 پیام بالا رو برای دوستات و گروه هایی که میشناسی فوروارد کن\n'
        'یا لینک پایین رو توی شبکه های اجتماعیت پخش کن،'
        'تا بقیه بتونن بهت پیام ناشناس بفرستن.\n\n'
        f'{link}'),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'برای اینستاگرام 📷',
                callback_data='user_link_instagram'
            ),
            InlineKeyboardButton(
                'برای تویتر 🕊',
                callback_data='user_link_twitter'
            ),
        ]])
    )


@require_user_data
async def user_link_extra(update: Update, ctx: Ctx, user_data: UserModel):
    platform = update.callback_query.data[10:]
    link = get_link(user_data.row_id, ctx.bot.username)

    if platform == 'twitter':
        file_id = config['user_link_twitter_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های توییترت برات پیام ناشناش بفرستن؟ 🤔\n\n'
            'کافیه لینک ناشناس رو کپی کنی و توی قسمت گفته شده در '
            f'پروفایلت وارد کنی ☝️)\n\nلینک مخصوصت 👉 {link}'
        ))
    elif platform == 'instagram':
        file_id = config['user_link_instagram_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های اینستاگرامت برات پیام ناشناش بفرستن؟ 🤔\n\n'
            'کافیه لینک ناشناس رو کپی کنی و توی قسمت گفته شده در '
            f'پروفایلت وارد کنی ☝️)\n\nلینک مخصوصت 👉 {link}'
        ))


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
        f'سن خود را وارد کنید. \nبین {AGE_RANGE[0]} تا {AGE_RANGE[1]} سال.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_edit_profile'
        )]])
    )

    ctx.user_data['user_profile_message_id'] = update.effective_message.id
    logging.info('edit age')
    logging.info(json.dumps(ctx.user_data))
    return 'EDIT_AGE'


@require_user_data
async def user_set_age(update: Update, ctx: Ctx, user_data: UserModel):
    logging.info('set age')
    logging.info(json.dumps(ctx.user_data))
    error_msg_id = ctx.user_data.get('user_set_age_error_message_id')

    try:
        age = int(update.effective_message.text)
        if age < AGE_RANGE[0] or age > AGE_RANGE[1]:
            raise ValueError('invalid age rage')
    except Exception:
        await update.effective_message.delete()

        if error_msg_id is None:
            em = await update.effective_message.reply_text(
                'خطا! پیام باید یک عدد بین '
                f'{AGE_RANGE[0]} تا {AGE_RANGE[1]} باشد. ❌'
            )
            ctx.user_data['user_set_age_error_message_id'] = em.id

        return

    msg_id = ctx.user_data.pop('user_profile_message_id', None)

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


''' edit name  '''


@require_user_data
async def user_edit_name(update: Update, ctx: Ctx, user_data: UserModel):

    await update.effective_message.edit_caption(
        'نام خود را ارسال کنید.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_edit_profile'
        )]])
    )

    ctx.user_data['user_profile_message_id'] = update.effective_message.id

    logging.info('edit name')
    logging.info(json.dumps(ctx.user_data))

    return 'EDIT_NAME'


@require_user_data
async def user_set_name(update: Update, ctx: Ctx, user_data: UserModel):
    logging.info('set name')
    logging.info(json.dumps(ctx.user_data))
    error_msg_id = ctx.user_data.get('user_set_name_error_message_id')

    try:
        name = update.effective_message.text
        name_len = len(name)
        if name_len < NAME_RANGE[0] or name_len > NAME_RANGE[1]:
            raise ValueError('invalid name length')
    except Exception:
        await update.effective_message.delete()

        if error_msg_id is None:
            em = await update.effective_message.reply_text(
                'خطا! طول نام باید بین '
                f'{NAME_RANGE[0]} و {NAME_RANGE[1]} باشد. ❌'
            )
            ctx.user_data['user_set_name_error_message_id'] = em.id

        return

    msg_id = ctx.user_data.pop('user_profile_message_id', None)

    await update_user(user_data.user_id, name=name)
    user_data.name = name
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
        await update.effective_message.reply_text('نام شما ثبت شد. ✅')

    if error_msg_id:
        await ctx.bot.delete_message(chat_id, error_msg_id)

    return ConversationHandler.END


@require_user_data
async def cancel_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        reply_markup=profile_keyboard
    )

    ctx.user_data.pop('user_profile_message_id', None)
    ctx.user_data.pop('user_set_age_error_message_id', None)

    return ConversationHandler.END
