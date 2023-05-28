

from database import get_user, get_user_count, update_user
from dependencies import require_admin
from telegram import Update
from telegram.ext import ContextTypes

Ctx = ContextTypes.DEFAULT_TYPE


@require_admin
async def get_file_id(update: Update, ctx: Ctx):
    if update.message.photo:
        await update.message.reply_html(
            'photo: \n'
            f'<code>{update.message.photo[0].file_id}</code>'
        )

    if update.message.video:
        await update.message.reply_html(
            'video: \n'
            f'<code>{update.message.video.file_id}</code>'
        )

    if update.message.animation:
        await update.message.reply_html(
            'animation: \n'
            f'<code>{update.message.animation.file_id}</code>'
        )


@require_admin
async def get_user_score(update: Update, ctx: Ctx):
    if not ctx.args:
        await update.effective_message.reply_text(
            'Error ❌\n/user_score <code>\n'
            '/user_score <code> set 12'
        )
        return

    user_data = await get_user(None, ctx.args[0])
    if user_data is None:
        await update.effective_message.reply_text(
            f'Error ❌\nuser with code {ctx.args[0]} was not found'
        )
        return

    await update.effective_message.reply_html(
        'User: \n'
        f'    id: <code>{user_data.user_id}</code>\n'
        f'    name: {user_data.name}\n'
        f'    invite score: {user_data.invite_score}\n🐧'
    )

    if len(ctx.args) == 3 and ctx.args[1] == 'set':
        try:
            new_score = int(ctx.args[2])
            await update_user(
                user_data.user_id,
                invite_score=new_score
            )
            await update.effective_message.reply_text(
                f'Ok ✅\nuser invite score was set to: {new_score} 🤡'
            )
        except Exception:
            await update.effective_message.reply_text(
                f'Error ❌\ninvalid invite score: {ctx.args[2]}'
            )


@require_admin
async def stats(update: Update, ctx: Ctx):
    users = await get_user_count()
    await update.effective_message.reply_text(
        f'total users: {users}'
    )
