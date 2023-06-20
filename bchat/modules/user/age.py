

from db.user import user_update
from deps import require_user_data
from models.user import UserModel, UserTable
from modules.common import delete_message
from settings import AGE_RANGE
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ConversationHandler
from telegram.ext import MessageHandler, filters

from .common import AGE_ERROR_MSG_KEY, EDIT_AGE_TRG, H_CANCEL_EDIT_PROFILE
from .common import IKB_EDIT_CANCEL, IKB_PROFILE, PROFILE_MSG_KEY, Ctx
from .common import get_profile_text


@require_user_data
async def user_edit_age(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()
    await update.effective_message.edit_caption(
        f'سن خود را وارد کنید. \nبین {AGE_RANGE[0]} تا {AGE_RANGE[1]} سال.',
        reply_markup=IKB_EDIT_CANCEL
    )

    ctx.user_data[PROFILE_MSG_KEY] = update.effective_message.id
    return 'EDIT_AGE'


@require_user_data
async def user_set_age(update: Update, ctx: Ctx, state: UserModel):
    error_msg_id = ctx.user_data.get(AGE_ERROR_MSG_KEY)
    chat_id = update.effective_message.chat_id
    msg = update.effective_message

    try:
        age = int(msg.text or '0')
        if age < AGE_RANGE[0] or age > AGE_RANGE[1]:
            raise ValueError(
                'خطا! پیام باید یک عدد بین '
                f'{AGE_RANGE[0]} تا {AGE_RANGE[1]} باشد. ❌'
            )
    except ValueError as e:
        await delete_message(ctx, chat_id, msg.id)

        if error_msg_id is None:
            em = await msg.reply_text(str(e))
            ctx.user_data[AGE_ERROR_MSG_KEY] = em.id

        return

    await user_update(UserTable.user_id == state.user_id, age=age)
    state.age = age

    profile_msg_id = ctx.user_data.pop(PROFILE_MSG_KEY, None)
    if profile_msg_id:
        await ctx.bot.edit_message_caption(
            chat_id,
            message_id=profile_msg_id,
            caption=get_profile_text(state, ctx.bot.username),
            parse_mode=ParseMode.HTML,
            reply_markup=IKB_PROFILE
        )
        await delete_message(ctx, chat_id, msg.id)
    else:
        await msg.reply_text('سن شما ثبت شد. ✅')

    if error_msg_id:
        ctx.user_data.pop(AGE_ERROR_MSG_KEY, None)
        await delete_message(ctx, chat_id, error_msg_id)

    return ConversationHandler.END


H_AGE_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        CallbackQueryHandler(
            user_edit_age,
            pattern=f'^{EDIT_AGE_TRG}$'
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
    fallbacks=H_CANCEL_EDIT_PROFILE,
)
