

from database import get_user, get_user_count, update_user
from dependencies import require_admin
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

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
        f'    total score: {user_data.total_score}\n🐧'
        f'    used  score: {user_data.used_score}\n🐧'
    )

    if len(ctx.args) >= 3 and ctx.args[1] == 'set':
        try:
            if len(ctx.args) > 3 and ctx.args[3] == 'total':
                await update_user(
                    user_data.user_id, total_score=int(ctx.args[2])
                )
            else:
                new_score = min(int(ctx.args[2]), user_data.total_score)
                await update_user(
                    user_data.user_id,
                    used_score=new_score
                )
            await update.effective_message.reply_text(
                'Ok ✅\nuser score was updated'
            )
        except Exception:
            await update.effective_message.reply_text(
                f'Error ❌\ninvalid score: {ctx.args[2]}'
            )


@require_admin
async def stats(update: Update, ctx: Ctx):
    users = await get_user_count()
    await update.effective_message.reply_text(
        f'total users: {users}'
    )


@require_admin
async def help_cmd(update: Update, ctx: Ctx):
    await update.effective_message.reply_text(
        '/help -> for this message\n'
        '/stats -> user count\n'
        '/user_score <code> -> get the user score\n'
        '/user_score <code> set 12 -> set the user used score\n'
        '/user_score <code> set 12 total -> set the user total score\n'
        '/channels -> get list of channels'
    )


@require_admin
async def cancel(update: Update, ctx: Ctx):
    await update.effective_message.reply_text('canceled.')
    return ConversationHandler.END
