

import logging

from database import get_user
from deps import require_admin
from settings import HOME_DIR
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import NetworkError, TelegramError
from telegram.ext import CallbackQueryHandler, ChatMemberHandler
from telegram.ext import CommandHandler, ContextTypes, ConversationHandler
from telegram.ext import MessageHandler, filters
from utils import config

from gshare import DbDict

rq_channels = DbDict(HOME_DIR / 'channels.json')

Ctx = ContextTypes.DEFAULT_TYPE


async def chat_member_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    cid = str(chat.id)
    if cid not in rq_channels:
        return

    chat_member = update.chat_member.new_chat_member
    user_data = await get_user(chat_member.user.id)

    if chat_member.status == 'member' and user_data:
        rq_channels[cid]['amount'] += 1

        if (
            rq_channels[cid]['limit'] > 1 and
            rq_channels[cid]['amount'] >= rq_channels[cid]['limit']
        ):
            rq_channels[cid]['enable'] = False

        rq_channels.save()


async def my_chat_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    e = update.my_chat_member
    status = e.new_chat_member.status
    user_id = e.from_user.id
    name = e.chat.title

    if e.chat.type not in ['channel', 'supergroup']:
        # await ctx.bot.leave_chat(e.chat.id)
        return

    if status == 'administrator':
        rq_channels[str(e.chat.id)] = {
            'enable': False,
            'amount': 0,
            'limit': -1
        }

        await ctx.bot.send_message(
            user_id,
            f'channel {name} was added ✅'
        )
    else:
        rq_channels.pop(str(e.chat.id), None)
        if status not in ['left', 'kicked']:
            await ctx.bot.leave_chat(e.chat.id)


async def get_keyboard_chats(ctx: Ctx):
    btns = []

    for cid, cval in rq_channels.items():
        cid = int(cid)
        enable = '✅' if cval['enable'] else '❌'
        chat = await ctx.bot.get_chat(cid)
        if not chat.invite_link:
            enable = '⚠'

        btns.append([
            InlineKeyboardButton(
                chat.title,
                url=chat.invite_link or 't.me/i007c'
            ),
        ])
        btns.append([
            InlineKeyboardButton(
                f'{cval["amount"]}/{cval["limit"]}',
                callback_data=f'set_rq_channel_limit#{chat.id}'
            ),
            InlineKeyboardButton(
                enable,
                callback_data=f'toggle_rq_channel#{chat.id}'
            ),
            InlineKeyboardButton(
                '⛔', callback_data=f'leave_rq_channel#{chat.id}'
            )
        ])

    return InlineKeyboardMarkup(btns)


@require_admin
async def rq_channel_query(update: Update, ctx: Ctx):
    query = update.callback_query
    await query.answer()

    if not query.data or not query.message:
        return

    data = query.data.split('#')

    if len(data) != 2:
        return

    action, cid = data

    if cid not in rq_channels:
        return

    if action == 'toggle_rq_channel':
        rq_channels[cid]['enable'] = not rq_channels[cid]['enable']
        rq_channels.save()

    elif action == 'leave_rq_channel':
        if (await ctx.bot.leave_chat(int(cid))):
            rq_channels.pop(cid, None)

    elif action == 'set_rq_channel_limit':
        ctx.user_data['rq_channel_id'] = cid
        await update.effective_message.reply_text(
            'ok. send the limit:\n'
            '/cancel'
        )
        return 'EDIT_RQ_CH_LIMIT'
    else:
        return

    await query.edit_message_reply_markup(await get_keyboard_chats(ctx))


@require_admin
async def rq_channel_set_limit(update: Update, ctx: Ctx):
    cid = ctx.user_data.pop('rq_channel_id', None)

    if update.message.text == '/cancel':
        await update.effective_message.reply_text('Canceled.')
        return ConversationHandler.END

    if cid in rq_channels:
        try:
            rq_channels[cid]['limit'] = int(update.message.text)
            rq_channels.save()
            await update.effective_message.reply_text('Ok 🪐')
        except Exception:
            await update.effective_message.reply_text('Error ❌')

    return ConversationHandler.END


@require_admin
async def channel_list(update: Update, ctx: Ctx):
    await update.message.reply_text(
        'list of all channels',
        reply_markup=await get_keyboard_chats(ctx)
    )


def require_joined(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.effective_message or not update.effective_user:
            return

        not_joined = []
        user = update.effective_user

        if user.is_bot:
            return

        if user.id in config['ADMINS']:
            await func(update, ctx)
            return

        for cid, cval in rq_channels.items():
            cid = int(cid)
            if not cval['enable']:
                continue

            try:
                member = await ctx.bot.get_chat_member(cid, user.id)

                if member.status in ['left', 'kicked']:
                    chat = await ctx.bot.get_chat(cid)
                    if not chat.invite_link:
                        continue
                    not_joined.append([
                        InlineKeyboardButton(
                            chat.title, url=chat.invite_link
                        )
                    ])

            except NetworkError:
                continue
            except TelegramError as e:
                logging.exception(e)
                # channel_remove(chat_id)
                continue

        if not_joined:
            await update.effective_message.reply_text(
                'اول مطمئن شوید که در کانال های زیر عضو شدید.',
                reply_markup=InlineKeyboardMarkup(not_joined)
            )

        else:
            await func(update, ctx)

    return decorator


@require_admin
async def cancel(update: Update, ctx: Ctx):
    await update.effective_message.reply_text('canceled.')
    return ConversationHandler.END


HANDLERS_CHANNELS = [
    CommandHandler(['channels'], channel_list),
    CallbackQueryHandler(
        rq_channel_query,
        pattern='^(toggle_rq_channel|leave_rq_channel)#(-|)[0-9]+$',
        block=False
    ),
    ConversationHandler(
        per_message=False,
        entry_points=[
            CallbackQueryHandler(
                rq_channel_query,
                pattern='^set_rq_channel_limit#(-|)[0-9]+$'
            ),
        ],
        states={
            'EDIT_RQ_CH_LIMIT': [
                MessageHandler(
                    filters.ChatType.PRIVATE,
                    rq_channel_set_limit,
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                'cancel', cancel,
            ),
        ],
    ),
    ChatMemberHandler(
        chat_member_update, ChatMemberHandler.CHAT_MEMBER
    ),
    ChatMemberHandler(
        my_chat_update, ChatMemberHandler.MY_CHAT_MEMBER
    ),

]
