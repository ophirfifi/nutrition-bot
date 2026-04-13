"""
OrchestratorAgent — single gateway for all user messages.
1. Distress guard (keyword scan, sync, before any LLM call)
2. Routes: photo → nutrition, text → LLM decides sub-agent
3. Logs all interactions to Firestore
"""
import json
import logging

from agents.base_agent import BaseAgent
from agents.habits import HabitsAgent
from agents.motivation import MotivationAgent
from agents.nutrition import NutritionAgent
from database.models import InteractionModel, UserModel
from database.repositories import interactions as interaction_repo

logger = logging.getLogger(__name__)

# ── Distress detection ─────────────────────────────────────────────────────────
# Hebrew patterns indicating potential distress / disordered eating
DISTRESS_PATTERNS = [
    "שונא את הגוף שלי",
    "שונאת את הגוף שלי",
    "שונא את עצמי",
    "שונאת את עצמי",
    "לא אוכל כלום",
    "לא אוכלת כלום",
    "לא רוצה לאכול",
    "לא רוצה לאכולת",
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

SYSTEM_PROMPT = """אתה האורקסטרטור של "נוטרי" — אפליקציית תזונה חכמה לנוער.

תפקידך: לקרוא את הודעת המשתמש ולהחליט מה לעשות איתה.

פרופיל המשתמש:
{user_profile}

החזר **אך ורק** JSON תקין:
{{
  "action": "direct" | "nutrition" | "motivation" | "habits",
  "response": "תגובה ישירה (חובה אם action=direct, אחרת null)"
}}

בחירת action:
- direct   → שיחת חולין, ברכות, שאלות כלליות שלא קשורות לאוכל/מוטיבציה/הרגלים
- nutrition → דיבור על אוכל ספציפי, מה אכלו, מתכון, מה לאכול
- motivation → רגש, קושי, הצלחה, "עשיתי טוב?", עידוד
- habits    → מים, שתייה, streak, ניקוד, כמה ארוחות היום

כללים:
- תגובת direct: עברית קלילה, 1-3 משפטים, עם אמוג'ים
- אין קלוריות, משקל, BMI — לעולם
"""


class OrchestratorAgent(BaseAgent):

    def __init__(self) -> None:
        super().__init__()
        self.nutrition = NutritionAgent()
        self.motivation = MotivationAgent()
        self.habits = HabitsAgent()

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

        # ── Photo → always nutrition ───────────────────────────────
        if photo_base64:
            response = await self.nutrition.analyze_meal(
                user=user,
                text_description=message_text,
                photo_base64=photo_base64,
                media_type=media_type,
            )
            await self._log(user.telegram_id, "outbound", response, "nutrition")
            return response

        # ── Route text message via LLM ─────────────────────────────
        system = SYSTEM_PROMPT.format(user_profile=self._profile(user))
        raw = await self.call_claude(
            system=system,
            messages=[{"role": "user", "content": message_text}],
            max_tokens=512,
        )

        try:
            data = json.loads(self._strip_codeblock(raw))
            action = data.get("action", "direct")
        except (json.JSONDecodeError, KeyError):
            logger.warning("Orchestrator returned non-JSON: %.200s", raw)
            await self._log(user.telegram_id, "outbound", raw, "orchestrator")
            return raw

        if action == "direct":
            response = data.get("response") or "סבבה! 👍"
        elif action == "nutrition":
            response = await self.nutrition.analyze_meal(
                user=user, text_description=message_text
            )
        elif action == "motivation":
            recent = await interaction_repo.get_recent(user.telegram_id, limit=10)
            response = await self.motivation.process(
                user=user, message_text=message_text, recent_history=recent
            )
        elif action == "habits":
            response = await self.habits.process_message(
                user=user, message_text=message_text
            )
        else:
            response = data.get("response") or "סבבה! 👍"

        await self._log(user.telegram_id, "outbound", response, "orchestrator")
        return response

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _strip_codeblock(text: str) -> str:
        """Remove markdown code block wrappers (```json...```) from LLM output."""
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
                "sport_type": user.sport_type,
                "eating_habits": user.eating_habits,
            },
            ensure_ascii=False,
        )

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
