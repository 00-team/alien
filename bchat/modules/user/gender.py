

from db.user import user_update
from deps import require_user_data
from models import GENDER_DISPLAY, Genders, UserModel, UserTable
from models import gender_pattern
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ConversationHandler

from .common import EDIT_GENDER_TRG, H_CANCEL_EDIT_PROFILE, IKB_PROFILE
from .common import PROFILE_EDIT_CANCEL_TGR, Ctx, get_profile_text


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
        'لغو ❌', callback_data=PROFILE_EDIT_CANCEL_TGR
    )])

    await update.effective_message.edit_reply_markup(
        InlineKeyboardMarkup(keyboard)
    )

    return 'EDIT_GENDER'


@require_user_data
async def user_set_gender(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    gender = int(update.callback_query.data[12:])

    await user_update(
        UserTable.user_id == state.user_id,
        gender=gender
    )
    state.gender = gender

    await update.effective_message.edit_caption(
        get_profile_text(state, ctx.bot.username),
        parse_mode=ParseMode.HTML,
        reply_markup=IKB_PROFILE
    )

    return ConversationHandler.END


H_GENDER_CONV = ConversationHandler(
    per_message=True,
    entry_points=[
        CallbackQueryHandler(
            user_edit_gender,
            pattern=f'^{EDIT_GENDER_TRG}$'
        ),
    ],
    states={
        'EDIT_GENDER': [CallbackQueryHandler(
            user_set_gender,
            pattern=f'^user_gender_({gender_pattern})$'
        )],
    },
    fallbacks=H_CANCEL_EDIT_PROFILE,
)
