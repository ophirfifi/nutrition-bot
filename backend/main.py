"""
FastAPI entry point.
  POST /webhook/{secret}     — Telegram webhook
  GET  /health               — health check
  GET  /api/dashboard/{tid}  — dashboard summary
  GET  /api/health-history/{tid} — score history (last 30 days)
  GET  /api/meals/{tid}      — recent meals
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

from bot.app import create_application
from config import settings
from database.connection import init_firebase
from database.repositories import meals as meal_repo
from database.repositories import scores as score_repo
from database.repositories import users as user_repo
from scheduler.jobs import start_scheduler

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_app

    init_firebase()

    if settings.skip_telegram:
        logger.warning("SKIP_TELEGRAM=true — bot and scheduler disabled (local dev mode)")
        yield
        return

    _bot_app = create_application()
    await _bot_app.initialize()
    await _bot_app.start()

    webhook_url = f"{settings.webhook_base_url}/webhook/{settings.telegram_webhook_secret}"
    await _bot_app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info("Webhook set: %s", webhook_url)

    start_scheduler(_bot_app)

    yield

    await _bot_app.stop()
    await _bot_app.shutdown()
    logger.info("Bot stopped")


app = FastAPI(title="NutriBot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to dashboard domain in production
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Telegram webhook ───────────────────────────────────────────────────────────

@app.post("/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request) -> Response:
    if secret != settings.telegram_webhook_secret:
        return Response(status_code=403)
    if _bot_app is None:
        return Response(status_code=503)
    data = await request.json()
    update = Update.de_json(data, _bot_app.bot)
    await _bot_app.process_update(update)
    return Response(status_code=200)


# ── Health check ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── Dashboard API ──────────────────────────────────────────────────────────────

@app.get("/api/dashboard/{telegram_id}")
async def get_dashboard(telegram_id: int):
    user = await user_repo.get(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    today = datetime.utcnow().date().isoformat()
    score = await score_repo.get(telegram_id, today)
    streak = await score_repo.calculate_streak(telegram_id)
    today_meals = await meal_repo.get_today(telegram_id)

    return {
        "name": user.name,
        "today": {
            "health_score": score.health_score if score else 0,
            "meals_count": score.meals_count if score else len(today_meals),
            "water_intake": score.water_intake if score else 0,
            "junk_count": score.junk_count if score else 0,
        },
        "streak": streak,
        "onboarding_complete": user.onboarding_complete,
    }


@app.get("/api/health-history/{telegram_id}")
async def get_health_history(telegram_id: int, days: int = 30):
    user = await user_repo.get(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    history = await score_repo.get_history(telegram_id, days=days)
    return [
        {"date": s.date, "health_score": s.health_score, "streak_days": s.streak_days}
        for s in history
    ]


@app.get("/api/meals/{telegram_id}")
async def get_meals(telegram_id: int, limit: int = 10):
    user = await user_repo.get(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recent = await meal_repo.get_recent(telegram_id, limit=limit)
    return [
        {
            "id": m.id,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "rating": m.rating,
            "description": m.description,
            "feedback_text": m.feedback_text,
            "categories": m.categories,
        }
        for m in recent
    ]
