"""
APScheduler jobs:
  08:00 — morning message to all users
  13:00 — lunch check-in
  20:00 — evening recap
  00:05 — calculate & persist daily Health Scores
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application

from agents.habits import HabitsAgent
from agents.orchestrator import OrchestratorAgent
from database.connection import get_db
from database.models import UserModel

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

MORNING_MSG = (
    "☀️ בוקר טוב {name}! היום שים לב לשתות 6–8 כוסות מים 💧\n"
    "מה אתה מתכנן לאכול היום?"
)
LUNCH_MSG = "🌤 אכלת כבר משהו מסודר? שלח לי תמונה ואני אתן פידבק 😊"
EVENING_MSG = "🌙 איך הלך היום? אכלת כמו שתכננת? ספר לי 💬"


async def _get_all_users() -> list[UserModel]:
    """Fetch all users with completed onboarding."""
    db = get_db()
    col = db.collection("users").where("onboarding_complete", "==", True)
    result = []
    async for doc in col.stream():
        try:
            result.append(UserModel(**doc.to_dict()))
        except Exception as exc:
            logger.error("Failed to parse user doc %s: %s", doc.id, exc, exc_info=True)
    return result


async def _send_to_all(app: Application, template: str) -> None:
    users = await _get_all_users()
    for user in users:
        try:
            text = template.format(name=user.name or "חבר")
            await app.bot.send_message(chat_id=user.telegram_id, text=text)
        except Exception as exc:
            logger.error("Failed to send scheduled msg to %s: %s", user.telegram_id, exc, exc_info=True)


async def morning_job(app: Application) -> None:
    logger.info("Running morning_job")
    await _send_to_all(app, MORNING_MSG)


async def lunch_job(app: Application) -> None:
    logger.info("Running lunch_job")
    await _send_to_all(app, LUNCH_MSG)


async def evening_job(app: Application) -> None:
    logger.info("Running evening_job")
    await _send_to_all(app, EVENING_MSG)


async def daily_score_job() -> None:
    """Calculate and persist Health Score for all active users."""
    logger.info("Running daily_score_job")
    habits = HabitsAgent()
    users = await _get_all_users()
    for user in users:
        try:
            score = await habits.calculate_and_save_daily_score(user.telegram_id, user)
            logger.info("Score saved for %s: %d", user.telegram_id, score.health_score)
        except Exception as exc:
            logger.error("Score calc failed for %s: %s", user.telegram_id, exc, exc_info=True)


def start_scheduler(app: Application) -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="Asia/Jerusalem")

    _scheduler.add_job(morning_job, "cron", hour=8, minute=0, args=[app], id="morning")
    _scheduler.add_job(lunch_job, "cron", hour=13, minute=0, args=[app], id="lunch")
    _scheduler.add_job(evening_job, "cron", hour=20, minute=0, args=[app], id="evening")
    _scheduler.add_job(daily_score_job, "cron", hour=0, minute=5, id="daily_score")

    _scheduler.start()
    logger.info("Scheduler started (4 jobs)")
    return _scheduler
