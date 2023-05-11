

from dependencies import require_admin
from telegram import Update


@require_admin
async def get_file_id(update: Update, ctx):
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
