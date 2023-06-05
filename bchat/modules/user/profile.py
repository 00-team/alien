
from deps import require_user_data
from models import UserModel
from settings import KW_PROFILE
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import MessageHandler, filters
from utils import config

from .common import IKB_PROFILE, Ctx, get_profile_text


@require_user_data
async def user_profile(update: Update, ctx: Ctx, state: UserModel):
    # user = update.effective_user
    # pictures = await user.get_profile_photos(limit=1)

    file_id = config['default_profile_picture']
    if state.picture:
        file_id = state.picture

    # if pictures.total_count > 0:
    #     file_id = pictures.photos[0][0].file_id

    await update.message.reply_photo(
        file_id, get_profile_text(state, ctx.bot.username),
        parse_mode=ParseMode.HTML,
        reply_markup=IKB_PROFILE
    )


H_PROFILE = [
    MessageHandler(
        filters.Text([KW_PROFILE]),
        user_profile, block=False
    )
]
