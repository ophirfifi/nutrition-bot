"""
HabitsAgent — streaks, Health Score, water intake tracking.

Health Score formula (0-100):
  Meal adherence   30%  — meals logged vs. recommended
  Nutritional variety 25% — food group coverage
  Water intake     20%  — glasses reported
  Junk avoidance   15%  — junk vs. total meals
  Reporting        10%  — messages/photos sent today
"""
import json
import logging
from datetime import datetime

from agents.base_agent import BaseAgent
from database.models import DailyScoreModel, UserModel
from database.repositories import interactions as interaction_repo
from database.repositories import meals as meal_repo
from database.repositories import scores as score_repo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה "נוטרי" — הצד של ניהול ההרגלים באפליקציית תזונה חכמה לנוער.

תפקידך:
- לענות על שאלות על מים, streak, ניקוד, התקדמות
- לתת פידבק על הרגלים בצורה חיובית

פרופיל המשתמש:
{user_profile}

נתוני היום:
{today_stats}

כללים:
- עברית קלילה עם אמוג'ים
- חיובי בלבד — streak שנשבר = "מחר מתחילים מחדש! 💪"
- אין קלוריות, משקל, BMI

החזר **אך ורק** JSON:
{
  "response": "הודעה למשתמש",
  "water_glasses": null או מספר (אם המשתמש דיווח על שתייה)
}
"""


class HabitsAgent(BaseAgent):

    async def process_message(self, user: UserModel, message_text: str) -> str:
        today_stats = await self._get_today_stats(user)
        system = SYSTEM_PROMPT.format(
            user_profile=json.dumps(
                {"name": user.name, "sport_type": user.sport_type},
                ensure_ascii=False,
            ),
            today_stats=json.dumps(today_stats, ensure_ascii=False),
        )

        raw = await self.call_claude(
            system=system,
            messages=[{"role": "user", "content": message_text}],
            max_tokens=512,
        )

        try:
            data = json.loads(raw.strip())
            # Update water intake if reported
            if data.get("water_glasses"):
                await self._update_water(user, int(data["water_glasses"]))
            return data.get("response", raw)
        except (json.JSONDecodeError, KeyError):
            logger.warning("HabitsAgent returned non-JSON: %.200s", raw)
            return raw

    async def calculate_and_save_daily_score(self, telegram_id: int, user: UserModel) -> DailyScoreModel:
        """Calculate today's Health Score and persist to Firestore."""
        today = datetime.utcnow().date()
        today_meals = await meal_repo.get_today(telegram_id)
        today_interactions = await interaction_repo.get_recent(telegram_id, limit=50)

        recommended_meals = (
            (user.eating_habits or {}).get("meals_per_day", 3)
            if user.eating_habits
            else 3
        )
        meals_count = len(today_meals)
        junk_count = sum(1 for m in today_meals if m.rating == "red")

        # Load existing score to preserve water_intake (updated separately)
        existing = await score_repo.get(telegram_id, today.isoformat())
        water_intake = existing.water_intake if existing else 0

        # ── Component scores ──────────────────────────────────────
        # 30% — meal adherence
        meal_ratio = min(meals_count / max(recommended_meals, 1), 1.0)
        meal_score = round(meal_ratio * 30)

        # 25% — nutritional variety (coverage of 4 food groups)
        covered_groups = set()
        for meal in today_meals:
            cats = meal.categories or {}
            for group in ("protein", "carbs", "fat", "vegetables"):
                if cats.get(group):
                    covered_groups.add(group)
        variety_score = round((len(covered_groups) / 4) * 25)

        # 20% — water intake (target: 8 glasses)
        water_score = round(min(water_intake / 8, 1.0) * 20)

        # 15% — junk avoidance
        if meals_count > 0:
            junk_ratio = junk_count / meals_count
            junk_score = round((1 - junk_ratio) * 15)
        else:
            junk_score = 0

        # 10% — reporting (sent at least 1 message or photo today)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_reports = [
            i for i in today_interactions
            if i.direction == "inbound" and i.timestamp >= today_start
        ]
        reporting_score = 10 if today_reports else 0

        health_score = meal_score + variety_score + water_score + junk_score + reporting_score

        # ── Streak ────────────────────────────────────────────────
        streak = await score_repo.calculate_streak(telegram_id)

        score = DailyScoreModel(
            telegram_id=telegram_id,
            date=today.isoformat(),
            health_score=health_score,
            meals_count=meals_count,
            water_intake=water_intake,
            junk_count=junk_count,
            balance_score=variety_score,
            streak_days=streak,
        )
        await score_repo.upsert(score)
        logger.info("Saved daily score %d for user %s", health_score, telegram_id)
        return score

    async def _get_today_stats(self, user: UserModel) -> dict:
        today = datetime.utcnow().date().isoformat()
        score = await score_repo.get(user.telegram_id, today)
        streak = await score_repo.calculate_streak(user.telegram_id)
        meals = await meal_repo.get_today(user.telegram_id)
        return {
            "health_score": score.health_score if score else 0,
            "streak_days": streak,
            "meals_count": len(meals),
            "water_intake": score.water_intake if score else 0,
        }

    async def _update_water(self, user: UserModel, glasses: int) -> None:
        today = datetime.utcnow().date().isoformat()
        existing = await score_repo.get(user.telegram_id, today)
        new_score = DailyScoreModel(
            telegram_id=user.telegram_id,
            date=today,
            water_intake=glasses,
            health_score=existing.health_score if existing else 0,
            meals_count=existing.meals_count if existing else 0,
        )
        await score_repo.upsert(new_score)
