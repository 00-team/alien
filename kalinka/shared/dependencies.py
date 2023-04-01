
from telegram import Update
from telegram.ext import ContextTypes

import shared.logger

from .settings import ADMINS


def require_admin(func):
    async def decorator(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.from_user:
            return

        user = update.message.from_user
        if user.id in ADMINS:
            return await func(update, ctx)

    return decorator


__all__ = [
    'require_admin',
]
