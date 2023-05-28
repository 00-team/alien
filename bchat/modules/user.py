
import logging

from database import get_user, update_user
from dependencies import require_user_data
from models import GENDER_DISPLAY, Genders, UserModel
from settings import AGE_RANGE, NAME_RANGE
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler
from utils import config

Ctx = ContextTypes.DEFAULT_TYPE
profile_keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            'تغییر جنسیت 👤', callback_data='user_edit_gender'
        ),
        InlineKeyboardButton(
            'تغییر سن 🪪', callback_data='user_edit_age'
        ),
        InlineKeyboardButton(
            'تغییر نام ✏', callback_data='user_edit_name'
        ),
    ],
    [
        InlineKeyboardButton(
            'تغییر عکس پروفایل 🖼', callback_data='coming_soon'
        ),
        InlineKeyboardButton(
            'تغییر کد', callback_data='coming_soon'
        ),
    ]
])


def get_link(codename, bot_username):
    return f't.me/{bot_username}?start={codename}'


def get_profile_text(user_data: UserModel, bot_username):
    return (
        f'نام: {user_data.name}\n'
        f'جنسیت: {GENDER_DISPLAY[user_data.gender]}\n'
        f'سن: {user_data.age}\n'
        f'کد: `{user_data.codename}`\n'
        f'کاربران دعوت شده: `{user_data.invite_score}`\n\n'
        f'لینک ناشناس: {get_link(user_data.codename, bot_username)}\n\n'
    )


@require_user_data
async def user_link(update: Update, ctx: Ctx, user_data: UserModel):
    link = get_link(user_data.codename, ctx.bot.username)

    await update.effective_message.reply_text(
        f'سلام {user_data.name} هستم ✋😉\n\n'
        'لینک زیر رو لمس کن و هر حرفی که تو دلت هست یا هر'
        ' انتقادی که نسبت به من داری رو با خیال راحت بنویس و بفرست. '
        'بدون اینکه از اسمت باخبر بشم پیامت به من می رسه. خودتم می تونی '
        'امتحان کنی و از بقیه بخوای راحت و ناشناس بهت پیام بفرستن، حرفای'
        ' خیلی جالبی می شنوی!\n\n'
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
    await update.callback_query.answer()

    platform = update.callback_query.data[10:]
    link = get_link(user_data.codename, ctx.bot.username)

    if platform == 'twitter':
        file_id = config['user_link_twitter_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های تویتترت برات پیام ناشناس بفرستن؟ 🤔\n\n'
            'فقط کافیه لینک ناشناستو کپی کنی و توی قسمت گفته شده توی پروفایلت'
            f'وارد کنی. 👌\n\nلینک مخصوصت 👈 {link}'
        ))

    elif platform == 'instagram':
        file_id = config['user_link_instagram_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های اینستاگرامت برات پیام ناشناس بفرستن؟ 🤔\n\n'
            'فقط کافیه لینک ناشناستو کپی کنی و توی قسمت گفته شده توی پروفایلت'
            f'وارد کنی. 👌\n\nلینک مخصوصت 👈 {link}'
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
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=profile_keyboard
    )


@require_user_data
async def user_edit_gender(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()
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
    await update.callback_query.answer()
    gender = int(update.callback_query.data[12:])

    await update_user(user_data.user_id, gender=gender)
    user_data.gender = gender

    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=profile_keyboard
    )

    return ConversationHandler.END


@require_user_data
async def user_edit_age(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    await update.effective_message.edit_caption(
        f'سن خود را وارد کنید. \nبین {AGE_RANGE[0]} تا {AGE_RANGE[1]} سال.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_edit_profile'
        )]])
    )

    ctx.user_data['user_profile_message_id'] = update.effective_message.id

    return 'EDIT_AGE'


@require_user_data
async def user_set_age(update: Update, ctx: Ctx, user_data: UserModel):
    error_msg_id = ctx.user_data.get('user_set_age_error_message_id')

    try:
        age = int(update.effective_message.text)
        if age < AGE_RANGE[0] or age > AGE_RANGE[1]:
            raise ValueError('invalid age rage')
    except Exception:
        try:
            await update.effective_message.delete()
        except Exception as e:
            logging.exception(e)

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
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=profile_keyboard
        )
        try:
            await update.effective_message.delete()
        except Exception as e:
            logging.exception(e)
    else:
        await update.effective_message.reply_text('سن شما ثبت شد. ✅')

    if error_msg_id:
        ctx.user_data.pop('user_set_age_error_message_id', None)
        try:
            await ctx.bot.delete_message(chat_id, error_msg_id)
        except Exception as e:
            logging.exception(e)

    return ConversationHandler.END


''' edit name  '''


@require_user_data
async def user_edit_name(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    await update.effective_message.edit_caption(
        'نام خود را ارسال کنید.',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            'لغو ❌', callback_data='cancel_edit_profile'
        )]])
    )

    ctx.user_data['user_profile_message_id'] = update.effective_message.id

    return 'EDIT_NAME'


@require_user_data
async def user_set_name(update: Update, ctx: Ctx, user_data: UserModel):
    error_msg_id = ctx.user_data.get('user_set_name_error_message_id')

    try:
        name = update.effective_message.text
        name_len = len(name)
        if name_len < NAME_RANGE[0] or name_len > NAME_RANGE[1]:
            raise ValueError('invalid name length')
    except Exception:
        try:
            await update.effective_message.delete()
        except Exception as e:
            logging.exception(e)

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
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=profile_keyboard
        )
        try:
            await update.effective_message.delete()
        except Exception as e:
            logging.exception(e)
    else:
        await update.effective_message.reply_text('نام شما ثبت شد. ✅')

    if error_msg_id:
        ctx.user_data.pop('user_set_name_error_message_id', None)
        try:
            await ctx.bot.delete_message(chat_id, error_msg_id)
        except Exception as e:
            logging.exception(e)

    return ConversationHandler.END


@require_user_data
async def cancel_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=profile_keyboard
    )

    ctx.user_data.pop('user_profile_message_id', None)
    ctx.user_data.pop('user_set_age_error_message_id', None)

    return ConversationHandler.END


@require_user_data
async def toggle_user_block(update: Update, ctx: Ctx, user_data: UserModel):

    await update.callback_query.answer()

    uid = update.callback_query.data.split('#')[-1]
    target_user = await get_user(int(uid))
    if not target_user:
        await update.effective_message.reply_text('کاربر پیدا نشد. ❌')
        await update.effective_message.edit_reply_markup()
        return

    if user_data.block_list.pop(uid, False):
        await update.effective_message.reply_text(
            'کاربر آزادسازی گردید. 🟢'
        )
    else:
        user_data.block_list[uid] = {
            'codename': target_user.codename,
            'name': target_user.name,
        }
        await update.effective_message.reply_text(
            'کاربر بلاک شد. 🔴'
        )

    await update_user(user_data.user_id, block_list=user_data.block_list)


@require_user_data
async def show_saved_users(update: Update, ctx: Ctx, user_data: UserModel):

    if not user_data.saved_list:
        await update.effective_message.reply_text(
            'شما کاربری را ذخیر نکرده اید.'
        )
        return

    keyboard = []
    for uid, data in user_data.saved_list.items():
        keyboard.append([
            InlineKeyboardButton(
                'حذف کاربر ❌',
                callback_data=(
                    f'remove_saved_user#{uid}'
                )
            ),
            InlineKeyboardButton(
                data['name'],
                url=f't.me/{ctx.bot.username}?start={data["codename"]}'
            )
        ])

    await update.effective_message.reply_text(
        'کاربران ذخیره شده شما.',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@require_user_data
async def toggle_saved_user(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    uid = update.callback_query.data.split('#')[-1]
    target_user = await get_user(int(uid))
    if not target_user:
        await update.effective_message.reply_text('کاربر پیدا نشد. ❌')
        await update.effective_message.edit_reply_markup()
        return

    if user_data.saved_list.pop(uid, False):
        await update.effective_message.reply_text(
            'کاربر از لیست حذف شد. 🔴'
        )
    else:
        user_data.saved_list[uid] = {
            'codename': target_user.codename,
            'name': target_user.name,
        }
        await update.effective_message.reply_text(
            'کاربر ذخیره شد. ⭐'
        )

    await update_user(user_data.user_id, saved_list=user_data.saved_list)
