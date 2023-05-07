

from dependencies import require_admin
from telegram import Update


@require_admin
async def get_file_id(update: Update, ctx):
    if not update.message.photo:
        await update.message.reply_text('no photo.')

    await update.message.reply_html(
        f'<pre>{update.message.photo[0].file_id}</pre>'
    )
