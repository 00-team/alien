

from db.user import user_update
from deps import require_score, require_user_data
from models.user import UserModel, UserTable
from modules.common import delete_message
from settings import NAME_CHANGE_COST, NAME_RANGE
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ConversationHandler
from telegram.ext import MessageHandler, filters

from .common import EDIT_NAME_TRG, H_CANCEL_EDIT_PROFILE, IKB_EDIT_CANCEL
from .common import IKB_PROFILE, NAME_ERROR_MSG_KEY, PROFILE_MSG_KEY, Ctx
from .common import get_profile_text


@require_user_data
@require_score(NAME_CHANGE_COST, 'نام')
async def user_edit_name(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()
    await update.effective_message.edit_caption(
        f'برای تغییر نام {NAME_CHANGE_COST} امتیاز از حساب شما کسر می شود.\n\n'
        'نام خود را ارسال کنید.',
        reply_markup=IKB_EDIT_CANCEL
    )

    ctx.user_data[PROFILE_MSG_KEY] = update.effective_message.id
    return 'EDIT_NAME'


@require_user_data
@require_score(NAME_CHANGE_COST, 'نام')
async def user_set_name(update: Update, ctx: Ctx, state: UserModel):
    error_msg_id = ctx.user_data.get(NAME_ERROR_MSG_KEY)
    msg = update.effective_message

    try:
        name = msg.text
        name_len = len(name)
        if name_len < NAME_RANGE[0] or name_len > NAME_RANGE[1]:
            raise ValueError(
                'خطا! طول نام باید بین '
                f'{NAME_RANGE[0]} و {NAME_RANGE[1]} باشد. ❌'
            )

    except ValueError as e:
        await delete_message(ctx, msg.chat_id, msg.id)

        if error_msg_id is None:
            errro_msg = await msg.reply_text(str(e))
            ctx.user_data[NAME_ERROR_MSG_KEY] = errro_msg.id

        return

    await user_update(
        UserTable.user_id == state.user_id,
        used_score=state.used_score + NAME_CHANGE_COST
    )
    state.name = name
    state.used_score += NAME_CHANGE_COST

    profile_msg_id = ctx.user_data.pop(PROFILE_MSG_KEY, None)
    if profile_msg_id:
        await ctx.bot.edit_message_caption(
            msg.chat_id,
            message_id=profile_msg_id,
            caption=get_profile_text(state, ctx.bot.username),
            parse_mode=ParseMode.HTML,
            reply_markup=IKB_PROFILE
        )
        await delete_message(ctx, msg.chat_id, msg.id)

    else:
        await msg.reply_text('نام شما ثبت شد. ✅')

    if error_msg_id:
        ctx.user_data.pop(NAME_ERROR_MSG_KEY, None)
        await delete_message(ctx, msg.chat_id, error_msg_id)

    return ConversationHandler.END


H_NAME_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        CallbackQueryHandler(
            user_edit_name,
            pattern=f'^{EDIT_NAME_TRG}$'
        )
    ],
    states={
        'EDIT_NAME': [
            MessageHandler(
                filters.ChatType.PRIVATE,
                user_set_name,
            )
        ],
    },
    fallbacks=H_CANCEL_EDIT_PROFILE
)
