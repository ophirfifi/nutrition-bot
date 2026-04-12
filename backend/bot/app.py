"""
Builds the python-telegram-bot Application.
We use updater=None (webhook mode — FastAPI owns the HTTP server).
"""
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.handlers import handle_help, handle_photo, handle_start, handle_stats, handle_text
from config import settings


def create_application() -> Application:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .updater(None)  # no polling — FastAPI receives webhooks
        .build()
    )

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("stats", handle_stats))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app
