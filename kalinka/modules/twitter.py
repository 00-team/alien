

from shared.database import add_reply, del_reply, get_replys, load_json
from shared.database import update_active, update_search
from shared.dependencies import require_admin
from shared.settings import BOT_DATA_PATH
from shared.tools import format_with_emojis
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

ST = {}


def menu_keyboard():
    active = '🟢' if update_active() else '🔴'

    keyboard = [
        [InlineKeyboardButton(
            f'active: {active}',
            callback_data='toggle_active'
        )],
        [InlineKeyboardButton(
            'set search',
            callback_data='set_search'
        )],
        [InlineKeyboardButton(
            'add reply tweet',
            callback_data='add_reply_tweet'
        )],
    ]

    return InlineKeyboardMarkup(keyboard)


@require_admin
async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    bot_data = load_json(BOT_DATA_PATH)

    await msg.reply_text((
        f'Search Term: {update_search()}\n'
        f'Total Search: {bot_data["total_search"]}\n'
        f'Total Shilled: {len(bot_data["shilled"])}'
    ),
        reply_markup=menu_keyboard()
    )

    for idx, rtext in enumerate(get_replys()):
        await msg.reply_text(
            f'[{idx}] Reply Tweet:\n' + format_with_emojis(rtext),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    'Delete ❌', callback_data=f'del_reply#{idx}')
            ]])
        )


@require_admin
async def update_message(update: Update, ctx):
    msg = update.message
    user_id = update.message.from_user.id
    st = ST[user_id]
    text = msg.text[:4000]

    if st == 'set_search':
        term = update_search(text)
        await msg.reply_text(f'new search term: {term}')

    elif st == 'add_reply_tweet':
        try:
            await msg.reply_text('new reply:\n' + format_with_emojis(text))
            add_reply(text)
        except IndexError:
            await msg.reply_text("maximum number of emoji's is 10.")

    ST[user_id] = ''


@require_admin
async def cancel(update: Update, ctx):
    user_id = update.message.from_user.id
    ST[user_id] = ''
    await update.message.reply_text('Canceled. ')


async def query_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data or not query.message:
        return

    data = query.data
    user_id = query.from_user.id
    update_menu = False

    if data == 'toggle_active':
        update_active(True)
        update_menu = True

    elif data == 'set_search':
        ST[user_id] = 'set_search'
        await query.message.reply_text(
            'Send Search Term\n/cancel for cancelation.'
        )

    elif data == 'add_reply_tweet':
        ST[user_id] = 'add_reply_tweet'
        await query.message.reply_text(
            'Send Tweet Reply\n/cancel for cancelation.'
        )

    elif data.find('del_reply#') == 0:
        del_reply(int(data.split('#')[1]))
        await query.message.reply_text('Reply Tweet Deleted.')

    if update_menu:
        await query.edit_message_reply_markup(menu_keyboard())
