
from deps import require_user_data
from models.user import UserModel
from settings import KW_MY_LINK
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, MessageHandler, filters
from utils import config

from .common import Ctx, get_link


@require_user_data
async def user_link(update: Update, ctx: Ctx, state: UserModel):
    link = get_link(state.codename, ctx.bot.username)

    await update.effective_message.reply_text(
        f'سلام {state.name} هستم ✋😉\n\n'
        'لینک زیر رو لمس کن و هر حرفی که تو دلت هست یا هر'
        ' انتقادی که نسبت به من داری رو با خیال راحت بنویس و بفرست. '
        'بدون اینکه از اسمت باخبر بشم پیامت به من می رسه. خودتم می تونی '
        'امتحان کنی و از بقیه بخوای راحت و ناشناس بهت پیام بفرستن، حرفای'
        ' خیلی جالبی می شنوی!\n\n'
        f'👇👇\n{link}'
    )

    await update.effective_message.reply_text((
        '👆👆 پیام بالا رو برای دوستات و گروه هایی که میشناسی فوروارد کن\n'
        'یا لینک پایین رو توی شبکه های اجتماعیت پخش کن،'
        'تا بقیه بتونن بهت پیام ناشناس بفرستن.\n\n'
        f'{link}'),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                'برای اینستاگرام 📷',
                callback_data='user_link_instagram'
            ),
            InlineKeyboardButton(
                'برای تویتر 🕊',
                callback_data='user_link_twitter'
            ),
        ]])
    )


@require_user_data
async def user_link_extra(update: Update, ctx: Ctx, user_data: UserModel):
    await update.callback_query.answer()

    platform = update.callback_query.data[10:]
    link = get_link(user_data.codename, ctx.bot.username)

    if platform == 'twitter':
        file_id = config['user_link_twitter_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های تویتترت برات پیام ناشناس بفرستن؟ 🤔\n\n'
            'فقط کافیه لینک ناشناستو کپی کنی و توی قسمت گفته شده توی پروفایلت'
            f'وارد کنی. 👌\n\nلینک مخصوصت 👈 {link}'
        ))

    elif platform == 'instagram':
        file_id = config['user_link_instagram_video']
        await update.effective_message.reply_video(file_id, caption=(
            'میخوای دنبال کننده های اینستاگرامت برات پیام ناشناس بفرستن؟ 🤔\n\n'
            'فقط کافیه لینک ناشناستو کپی کنی و توی قسمت گفته شده توی پروفایلت'
            f'وارد کنی. 👌\n\nلینک مخصوصت 👈 {link}'
        ))


H_LINK = [
    MessageHandler(
        filters.Text([KW_MY_LINK]),
        user_link, block=False,
    ),
    CallbackQueryHandler(
        user_link,
        pattern='^user_link$',
        block=False
    ),
    CallbackQueryHandler(
        user_link_extra,
        pattern='^user_link_(.*)$',
        block=False
    )
]
