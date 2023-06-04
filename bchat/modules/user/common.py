from deps import require_user_data
from models import GENDER_DISPLAY, UserModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ContextTypes
from telegram.ext import ConversationHandler

Ctx = ContextTypes.DEFAULT_TYPE

PROFILE_EDIT_CANCEL_TGR = 'profile_edit_cancel'
PROFILE_MSG_KEY = 'user:profile:msg:id'
AGE_ERROR_MSG_KEY = 'user:age:error:msg:id'
NAME_ERROR_MSG_KEY = 'user:name:error:msg:id'
CODE_ERROR_MSG_KEY = 'user:code:error:msg:id'

EDIT_AGE_TRG = 'user:edit:age'
EDIT_NAME_TRG = 'user:edit:name'
EDIT_GENDER_TRG = 'user:edit:gender'
EDIT_CODE_TRG = 'user:edit:code'

IKB_PROFILE = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            'تغییر جنسیت 👤', callback_data=EDIT_GENDER_TRG
        ),
        InlineKeyboardButton(
            'تغییر سن 🪪', callback_data=EDIT_AGE_TRG
        ),
        InlineKeyboardButton(
            'تغییر نام ✏', callback_data=EDIT_NAME_TRG
        ),
    ],
    [
        InlineKeyboardButton(
            'تغییر عکس پروفایل 🖼', callback_data='coming_soon'
        ),
        InlineKeyboardButton(
            'تغییر کد 🔥', callback_data=EDIT_CODE_TRG
        ),
    ]
])


IKB_EDIT_CANCEL = InlineKeyboardMarkup([[
    InlineKeyboardButton(
        'لغو ❌', callback_data=PROFILE_EDIT_CANCEL_TGR
    )
]])


def get_link(codename, bot_username):
    return f't.me/{bot_username}?start={codename}'


def get_profile_text(user_data: UserModel, bot_username):
    return (
        f'نام: {user_data.name}\n'
        f'جنسیت: {GENDER_DISPLAY[user_data.gender]}\n'
        f'سن: {user_data.age}\n'
        f'کد: <code>{user_data.codename}</code>\n'
        f'امتیاز شما: {user_data.total_score}\n'
        f'امتیاز مصرف شده: {user_data.used_score}\n\n'
        f'لینک ناشناس: {get_link(user_data.codename, bot_username)}\n\n'
    )


@require_user_data
async def cancel_edit_profile(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    await update.effective_message.edit_caption(
        get_profile_text(user_data, ctx.bot.username),
        parse_mode=ParseMode.HTML,
        reply_markup=IKB_PROFILE
    )

    ctx.user_data.pop(PROFILE_MSG_KEY, None)
    ctx.user_data.pop(AGE_ERROR_MSG_KEY, None)

    return ConversationHandler.END


H_CANCEL_EDIT_PROFILE = [CallbackQueryHandler(
    cancel_edit_profile,
    pattern=f'^{PROFILE_EDIT_CANCEL_TGR}$'
)]
