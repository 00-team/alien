

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
            f'<pre>{update.message.photo[0].file_id}</pre>'
        )

    if update.message.video:
        await update.message.reply_html(
            'video: \n'
            f'<pre>{update.message.video.file_id}</pre>'
        )

    if update.message.animation:
        await update.message.reply_html(
            'animation: \n'
            f'<pre>{update.message.animation.file_id}</pre>'
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
        await update.effective_message.reply_html(
            f'Error ❌\nuser with code <pre>{ctx.args[0]}</pre> was not found'
        )
        return

    await update.effective_message.reply_html(
        'User: \n'
        f'\tid: {user_data.user_id}\n'
        f'\tname: {user_data.name}\n'
        f'\tinvite score: <pre>{user_data.invite_score}</pre>'
    )

    if len(ctx.args) == 3 and ctx.args[1] == 'set':
        try:
            new_score = int(ctx.args[2])
            await update_user(
                user_data.user_id,
                invite_score=new_score
            )
            await update.effective_message.reply_html(
                f'Ok ✅\nuser invite score was set to: <pre>{new_score}</pre>'
            )
        except Exception:
            await update.effective_message.reply_html(
                f'Error ❌\ninvalid invite score: <pre>{ctx.args[2]}</pre>'
            )


@require_admin
async def stats(update: Update, ctx: Ctx):
    users = await get_user_count()
    await update.effective_message.reply_text(
        f'total users: {users}'
    )
