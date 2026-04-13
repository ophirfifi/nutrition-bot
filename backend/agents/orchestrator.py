"""
OrchestratorAgent — single gateway for all user messages.
1. Distress guard (keyword scan, sync, before any LLM call)
2. Routes: photo → nutrition, text → smart conversational response
3. Logs all interactions to Firestore
"""
import json
import logging
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.nutrition import NutritionAgent
from database.models import InteractionModel, UserModel
from database.repositories import interactions as interaction_repo
from database.repositories import meals as meal_repo
from database.repositories import scores as score_repo

logger = logging.getLogger(__name__)

# ── Distress detection ─────────────────────────────────────────────────────────
DISTRESS_PATTERNS = [
    "שונא את הגוף שלי",
    "שונאת את הגוף שלי",
    "שונא את עצמי",
    "שונאת את עצמי",
    "לא אוכל כלום",
    "לא אוכלת כלום",
    "לא רוצה לאכול",
    "לא ראוי לאכול",
    "לא ראויה לאכול",
    "מרגיש רע עם עצמי",
    "מרגישה רע עם עצמי",
    "רוצה למות",
    "רוצה להיעלם",
    "אין לי כוח לחיות",
    "מתגעגע לאוכל בצורה קיצונית",
]

SAFETY_MESSAGE = """מרגיש שקשה לך עכשיו 💙

אתה לא לבד. אם אתה זקוק לעזרה, אפשר לפנות ל:
📞 **ער"ן** — עזרה ראשונה נפשית: **1201** (חינם, 24/7)

אני כאן אם תרצה לדבר 🤗"""

SYSTEM_PROMPT = """אתה "נוטרי" — בוט תזונה חכם ואישי לנוער.
אתה חבר אמיתי שעוזר עם תזונה, הרגלים, ומוטיבציה — לא רובוט קליני.

## פרופיל המשתמש
{user_profile}

## הנתונים של היום
{today_stats}

## כללים קשיחים
- דבר בעברית קלילה, כמו חבר, עם אמוג'ים
- לעולם לא לומר קלוריות, משקל, BMI, דיאטה, הגבלה
- חיובי ולא שיפוטי — תמיד
- תשובות קצרות: 2-4 משפטים מקסימום
- אם המשתמש ביצע הישג — חגוג איתו!
- אם המשתמש דילג על ארוחה — "סבבה, מחר יום חדש"
- אם המשתמש רעב — שאל מה אכל היום, תייעץ מה לאכול עכשיו, התייחס לשעה ולאימונים

## מה אתה יודע לעשות
1. **תזונה** — המלצות על מה לאכול, תגובה למה שאכלו, הסברים על ארוחות
   - אם מישהו אומר "אני רעב" — תשאל מה אכל היום, תמליץ מה כדאי לאכול עכשיו
   - אם מישהו מתאר ארוחה בטקסט — דרג (ירוק/צהוב/אדום) ותן פידבק
   - התאם לספורט: ספורטאי = צריך יותר פחמימות וחלבון
2. **מוטיבציה** — עידוד, חיזוקים, תמיכה רגשית
   - אם מישהו אומר "אכלתי שטויות" — אל תשפוט, תחזק
   - אם מישהו שואל "עשיתי טוב?" — ענה בכנות וחיובית
3. **הרגלים** — מים, streak, ניקוד, התקדמות
   - דווח על הנתונים של היום בצורה מעודדת
   - אם מדווח על שתייה (כמה כוסות מים) — רשום את המספר
4. **שיחה כללית** — ברכות, בדיחות, שאלות

## פורמט תגובה
החזר **אך ורק** JSON:
{{
  "response": "התגובה שלך למשתמש (עברית, 2-4 משפטים, אמוג'ים)",
  "water_glasses": null,
  "meal_report": null
}}

- water_glasses: מספר (אם המשתמש דיווח כמה כוסות שתה, אחרת null)
- meal_report: אובייקט עם rating/categories/description (אם המשתמש תיאר ארוחה, אחרת null)
  {{
    "rating": "green" | "yellow" | "red",
    "description": "תיאור קצר של הארוחה",
    "categories": {{"protein": true/false, "carbs": true/false, "fat": true/false, "vegetables": true/false}}
  }}
"""


class OrchestratorAgent(BaseAgent):

    def __init__(self) -> None:
        super().__init__()
        self.nutrition = NutritionAgent()

    async def process(
        self,
        user: UserModel,
        message_text: str,
        photo_base64: str | None = None,
        media_type: str = "image/jpeg",
    ) -> str:
        # ── Log inbound ────────────────────────────────────────────
        await self._log(
            user.telegram_id,
            "inbound",
            message_text,
            "orchestrator",
            msg_type="image" if photo_base64 else "text",
        )

        # ── Distress guard (sync keyword check) ───────────────────
        if message_text and self._is_distress(message_text):
            await self._log(
                user.telegram_id, "inbound", message_text, "orchestrator",
                msg_type="text", distress=True,
            )
            return SAFETY_MESSAGE

        # ── Photo → always nutrition agent (vision) ───────────────
        if photo_base64:
            response = await self.nutrition.analyze_meal(
                user=user,
                text_description=message_text,
                photo_base64=photo_base64,
                media_type=media_type,
            )
            await self._log(user.telegram_id, "outbound", response, "nutrition")
            return response

        # ── Text → smart conversational agent ─────────────────────
        recent = await interaction_repo.get_recent(user.telegram_id, limit=16)
        today_stats = await self._get_today_stats(user.telegram_id)

        system = SYSTEM_PROMPT.format(
            user_profile=self._profile(user),
            today_stats=today_stats,
        )

        # Build conversation history from recent interactions
        messages = self._build_history(recent) + [
            {"role": "user", "content": message_text}
        ]

        raw = await self.call_claude(
            system=system,
            messages=messages,
            max_tokens=1024,
        )

        try:
            data = json.loads(self._strip_codeblock(raw))
            response = data.get("response") or "סבבה! 👍"

            # Handle water report
            water = data.get("water_glasses")
            if water is not None and isinstance(water, (int, float)) and water > 0:
                await self._update_water(user.telegram_id, int(water))

            # Handle meal report from text
            meal = data.get("meal_report")
            if meal and isinstance(meal, dict) and meal.get("rating"):
                await self._save_text_meal(user, meal)

        except (json.JSONDecodeError, KeyError):
            logger.warning("Orchestrator returned non-JSON: %.200s", raw)
            response = raw

        await self._log(user.telegram_id, "outbound", response, "orchestrator")
        return response

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _strip_codeblock(text: str) -> str:
        t = text.strip()
        if t.startswith("```"):
            first_nl = t.index("\n") if "\n" in t else 3
            t = t[first_nl + 1:]
        if t.endswith("```"):
            t = t[:-3]
        return t.strip()

    @staticmethod
    def _is_distress(text: str) -> bool:
        t = text.lower()
        return any(pattern in t for pattern in DISTRESS_PATTERNS)

    @staticmethod
    def _profile(user: UserModel) -> str:
        return json.dumps(
            {
                "name": user.name,
                "age": user.age,
                "height": user.height,
                "sport_type": user.sport_type,
                "sport_frequency": user.sport_frequency,
                "eating_habits": user.eating_habits,
                "preferences": user.preferences,
                "triggers": user.triggers,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _build_history(recent_interactions: list) -> list[dict]:
        """Convert recent interactions to Claude messages format (oldest first)."""
        messages = []
        for inter in reversed(recent_interactions):
            role = "user" if inter.direction == "inbound" else "assistant"
            text = inter.message_text
            if not text:
                continue
            # Avoid consecutive messages with same role (Claude requirement)
            if messages and messages[-1]["role"] == role:
                messages[-1]["content"] += f"\n{text}"
            else:
                messages.append({"role": role, "content": text})
        return messages

    @staticmethod
    async def _get_today_stats(telegram_id: int) -> str:
        today_str = datetime.utcnow().date().isoformat()
        score = await score_repo.get(telegram_id, today_str)
        today_meals = await meal_repo.get_today(telegram_id)
        streak = await score_repo.calculate_streak(telegram_id)

        meal_descriptions = [
            f"- {m.description or 'ארוחה'} ({m.rating or '?'})"
            for m in today_meals
        ]

        return json.dumps(
            {
                "health_score": score.health_score if score else 0,
                "meals_count": len(today_meals),
                "meals_today": meal_descriptions or ["אין ארוחות עדיין"],
                "water_intake": score.water_intake if score else 0,
                "junk_count": score.junk_count if score else 0,
                "streak_days": streak,
                "current_hour": datetime.utcnow().strftime("%H:%M"),
            },
            ensure_ascii=False,
        )

    @staticmethod
    async def _update_water(telegram_id: int, glasses: int) -> None:
        from database.models import DailyScoreModel
        today_str = datetime.utcnow().date().isoformat()
        existing = await score_repo.get(telegram_id, today_str)
        if existing:
            existing.water_intake = max(existing.water_intake, glasses)
            await score_repo.upsert(existing)
        else:
            await score_repo.upsert(DailyScoreModel(
                telegram_id=telegram_id,
                date=today_str,
                water_intake=glasses,
            ))

    @staticmethod
    async def _save_text_meal(user: UserModel, meal_data: dict) -> None:
        from database.models import MealModel
        import uuid
        try:
            meal = MealModel(
                id=str(uuid.uuid4()),
                telegram_id=user.telegram_id,
                timestamp=datetime.utcnow(),
                description=meal_data.get("description"),
                categories=meal_data.get("categories"),
                rating=meal_data.get("rating"),
                feedback_text=None,
            )
            await meal_repo.create(meal)
        except Exception as exc:
            logger.error("Failed to save text meal: %s", exc, exc_info=True)

    @staticmethod
    async def _log(
        telegram_id: int,
        direction: str,
        text: str | None,
        agent_type: str,
        msg_type: str = "text",
        distress: bool = False,
    ) -> None:
        try:
            await interaction_repo.log(
                InteractionModel(
                    telegram_id=telegram_id,
                    direction=direction,
                    message_text=text,
                    agent_type=agent_type,
                    message_type=msg_type,
                    distress_flag=distress,
                )
            )
        except Exception as exc:
            logger.error("Failed to log interaction for %s: %s", telegram_id, exc, exc_info=True)
