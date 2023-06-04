
import string

from db.user import user_get, user_update
from deps import require_score, require_user_data
from models.user import UserModel, UserTable
from modules.common import delete_message
from settings import CODE_CHANGE_COST
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, ConversationHandler
from telegram.ext import MessageHandler, filters

from .common import CODE_ERROR_MSG_KEY, EDIT_CODE_TRG, H_CANCEL_EDIT_PROFILE
from .common import IKB_EDIT_CANCEL, IKB_PROFILE, PROFILE_MSG_KEY, Ctx
from .common import get_profile_text


@require_user_data
@require_score(CODE_CHANGE_COST, 'کد')
async def user_edit_code(update: Update, ctx: Ctx, state: UserModel):
    await update.callback_query.answer()
    await update.effective_message.edit_caption(
        f'برای تغییر کد {CODE_CHANGE_COST} امتیاز از حساب شما کسر می شود.\n\n'
        'کد مدنظر خود را ارسال کنید:',
        reply_markup=IKB_EDIT_CANCEL
    )

    ctx.user_data[PROFILE_MSG_KEY] = update.effective_message.id
    return 'EDIT_CODE'


@require_user_data
@require_score(CODE_CHANGE_COST, 'کد')
async def user_set_code(update: Update, ctx: Ctx, state: UserModel):
    msg = update.effective_message
    error_msg_id = ctx.user_data.get(CODE_ERROR_MSG_KEY)

    try:
        code = msg.text
        if len(code) > 25:
            raise ValueError('خطا! حداکثر طول کد 25 می باشد. ❌')

        for c in code:
            if c not in string.ascii_letters + string.digits + '_':
                raise ValueError(
                    'خطا! فقط حروف و اعداد انگلیسی قابل قبول می باشد. ❌'
                )

        others = await user_get(UserTable.codename == code)

        if others:
            raise ValueError('خطا! این کد قبلا استفاده شده. ❌')
    except ValueError as e:
        await delete_message(ctx, msg.chat_id, msg.id)

        if error_msg_id is None:
            error_msg = await msg.reply_text(str(e))
            ctx.user_data[CODE_ERROR_MSG_KEY] = error_msg.id
        else:
            await ctx.bot.edit_message_text(str(e), msg.chat_id, error_msg_id)

        return

    await user_update(
        UserTable.user_id == state.user_id,
        codename=code,
        used_score=state.used_score + CODE_CHANGE_COST
    )
    state.codename = code
    state.used_score += CODE_CHANGE_COST

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
        await msg.reply_text('کد شما ثبت شد. ✅')

    if error_msg_id:
        ctx.user_data.pop(CODE_ERROR_MSG_KEY, None)
        await delete_message(ctx, msg.chat_id, error_msg_id)

    return ConversationHandler.END


H_CODE_CONV = ConversationHandler(
    per_message=False,
    entry_points=[
        CallbackQueryHandler(
            user_edit_code,
            pattern=f'^{EDIT_CODE_TRG}$'
        )
    ],
    states={
        'EDIT_CODE': [
            MessageHandler(
                filters.ChatType.PRIVATE,
                user_set_code,
            )
        ],
    },
    fallbacks=H_CANCEL_EDIT_PROFILE,
)
