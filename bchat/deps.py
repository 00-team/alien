

from database import add_user, update_user_code
from db.user import user_get, user_update
from models import UserModel, UserTable
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler
from utils import config

Ctx = ContextTypes.DEFAULT_TYPE


def require_admin(func):
    async def decorator(update: Update, ctx: Ctx):
        user = update.effective_user

        if user.id in config['ADMINS']:
            return await func(update, ctx)

    return decorator


def require_user_data(func):
    async def decorator(update: Update, ctx: Ctx):
        user = update.effective_user
        if user.is_bot:
            return

        if user.id in [6147521442]:
            return

        user_data = await user_get(UserTable.user_id == user.id)

        if user_data is None:
            codename = await add_user(user.id, user.full_name)
            user_data = UserModel(
                user_id=user.id,
                name=user.full_name,
                age=20,
                gender=0,
                codename=codename,
                new_user=True,
            )

        if not user_data.codename:
            user_data.codename = await update_user_code(user_data.user_id)

        if user_data.admin_blocked:
            return

        if user_data.blocked_bot:
            await user_update(
                UserTable.user_id == user_data.user_id,
                blocked_bot=False
            )
            user_data.blocked_bot = False

        return await func(update, ctx, user_data)

    return decorator


def require_score(cost: int, text: str):
    def wrapper(func):
        async def decorator(update: Update, ctx: Ctx, state: UserModel):
            ava_score = state.total_score - state.used_score
            if ava_score < cost:
                await update.effective_message.reply_text(
                    (
                        f'حداقل امتیاز برای تغییر {text} '
                        f'{cost} امتیاز می باشد. ❌\n'
                        'هر فردی که به شما پیام ناشناس ارسال '
                        'کند 1 امتیاز محاسبه میشود.\n'
                        f'امتیاز قابل استفاده شما: {ava_score}'
                    ),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            'جمع آوری امتیاز 🌟',
                            callback_data='user_link'
                        )
                    ]])
                )

                return ConversationHandler.END

            return await func(update, ctx, state)

        return decorator

    return wrapper


__all__ = [
    'require_admin',
    'require_user_data',
    'require_score'
]
