"""
Telegram update handlers.
Flow per message:
  1. Get-or-create user from Firestore
  2. If onboarding incomplete → OnboardingAgent
  3. Else → OrchestratorAgent (distress guard + routing)
"""
import base64
import logging

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from agents.onboarding import OnboardingAgent
from agents.orchestrator import OrchestratorAgent
from config import settings
from database.models import UserModel
from database.repositories import users as user_repo

logger = logging.getLogger(__name__)

onboarding_agent = OnboardingAgent()
orchestrator = OrchestratorAgent()

HELP_TEXT = """*נוטרי — עזרה* 🥗

שלח לי:
📸 *תמונת אוכל* — אני אנתח ואדרג
💬 *טקסט חופשי* — על מה שאכלת, איך אתה מרגיש, כמה שתית
💧 כתוב "שתיתי X כוסות" לעדכון שתייה

פקודות:
/start — התחל מחדש
/stats — הניקוד שלך היום
/help — ההודעה הזו

🔗 דשבורד ההתקדמות שלך ייישלח אחרי ההרשמה
"""

STATS_NO_DATA = "עדיין אין נתונים להיום. שלח לי תמונה או תכתוב מה אכלת 😊"


async def _get_or_create_user(telegram_id: int) -> tuple[UserModel, bool]:
    return await user_repo.get_or_create(telegram_id)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, created = await _get_or_create_user(update.effective_user.id)
    welcome = await onboarding_agent.get_welcome_message()
    await update.message.reply_text(welcome)


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from database.repositories import scores as score_repo
    from datetime import datetime

    user, _ = await _get_or_create_user(update.effective_user.id)
    today = datetime.utcnow().date().isoformat()
    score = await score_repo.get(user.telegram_id, today)
    streak = await score_repo.calculate_streak(user.telegram_id)

    if not score:
        await update.message.reply_text(STATS_NO_DATA)
        return

    grade = _score_to_emoji(score.health_score)
    text = (
        f"*הניקוד שלך היום* {grade}\n\n"
        f"🏆 ניקוד בריאות: *{score.health_score}/100*\n"
        f"🔥 רצף ימים: *{streak}*\n"
        f"🍽 ארוחות: *{score.meals_count}*\n"
        f"💧 שתייה: *{score.water_intake}* כוסות\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, created = await _get_or_create_user(update.effective_user.id)
    message_text = update.message.text.strip()

    if not user.onboarding_complete:
        response = await onboarding_agent.process(user, message_text)
        # Refresh user after potential onboarding completion
        user = await user_repo.get(user.telegram_id) or user
    else:
        response = await orchestrator.process(user, message_text)

    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user, _ = await _get_or_create_user(update.effective_user.id)

    if not user.onboarding_complete:
        await update.message.reply_text(
            "קודם בוא נסיים את ההיכרות שלנו 😊 כתוב לי קצת כדי שנכיר!"
        )
        return

    # Download the highest-quality photo from Telegram
    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{tg_file.file_path}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(photo_url)
            resp.raise_for_status()
            photo_bytes = resp.content
    except Exception as exc:
        logger.error("Failed to download photo for user %s: %s", user.telegram_id, exc, exc_info=True)
        await update.message.reply_text(
            "😕 לא הצלחתי להוריד את התמונה. נסה לשלוח שוב?"
        )
        return

    photo_b64 = base64.b64encode(photo_bytes).decode()
    caption = update.message.caption or ""

    response = await orchestrator.process(
        user=user,
        message_text=caption,
        photo_base64=photo_b64,
        media_type="image/jpeg",
    )
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)


def _score_to_emoji(score: int) -> str:
    if score >= 75:
        return "🟢"
    if score >= 45:
        return "🟡"
    return "🔴"
