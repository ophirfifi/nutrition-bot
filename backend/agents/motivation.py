"""
MotivationAgent — emotional support, encouragement, distress detection.
"""
import json
import logging

from agents.base_agent import BaseAgent
from database.models import InteractionModel, UserModel
from database.repositories import interactions as interaction_repo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה "נוטרי" — הצד המוטיבציוני של אפליקציית תזונה חכמה לנוער.

תפקידך:
- לזהות דפוסים רגשיים ולהפיק חיזוקים
- לשלוח הודעות עידוד, לא לשפוט
- לזהות מצוקה ולהחזיר distress_detected: true

פרופיל המשתמש:
{user_profile}

היסטוריה אחרונה:
{recent_history}

כללים:
- עברית קלילה עם אמוג'ים
- חיובי בלבד, לא שיפוטי אף פעם
- אין קלוריות, משקל, BMI — לעולם
- תגובות קצרות (2-4 משפטים מקסימום)
- אם המשתמש ביצע הישג — חגוג איתו
- אם המשתמש דילג על ארוחה — "סבבה, מחר יום חדש"

החזר **אך ורק** JSON תקין:
{
  "response": "הודעה למשתמש",
  "distress_detected": false,
  "sentiment": "positive" | "neutral" | "negative"
}
"""

DISTRESS_SAFETY_MESSAGE = """מרגיש שקשה לך עכשיו 💙

אתה לא לבד. אם אתה זקוק לעזרה, אפשר לפנות ל:
📞 **ער"ן** — עזרה ראשונה נפשית: **1201** (חינם, 24/7)
📞 **ERAN** (English): **1201**

אני כאן אם תרצה לדבר 🤗"""


class MotivationAgent(BaseAgent):

    async def process(
        self,
        user: UserModel,
        message_text: str,
        recent_history: list[InteractionModel] | None = None,
    ) -> str:
        history_text = self._format_history(recent_history or [])
        system = SYSTEM_PROMPT.format(
            user_profile=self._format_profile(user),
            recent_history=history_text,
        )

        raw = await self.call_claude(
            system=system,
            messages=[{"role": "user", "content": message_text}],
            max_tokens=512,
        )

        try:
            data = json.loads(raw.strip())
            if data.get("distress_detected"):
                await self._flag_distress(user, message_text)
                return DISTRESS_SAFETY_MESSAGE
            return data.get("response", raw)
        except (json.JSONDecodeError, KeyError):
            logger.warning("MotivationAgent returned non-JSON: %.200s", raw)
            return raw

    async def _flag_distress(self, user: UserModel, message_text: str) -> None:
        interaction = InteractionModel(
            telegram_id=user.telegram_id,
            agent_type="motivation",
            direction="inbound",
            message_text=message_text,
            distress_flag=True,
        )
        try:
            await interaction_repo.log(interaction)
        except Exception as exc:
            logger.error("Failed to log distress for user %s: %s", user.telegram_id, exc, exc_info=True)

    @staticmethod
    def _format_profile(user: UserModel) -> str:
        return json.dumps(
            {"name": user.name, "age": user.age, "sport_type": user.sport_type},
            ensure_ascii=False,
        )

    @staticmethod
    def _format_history(history: list[InteractionModel]) -> str:
        if not history:
            return "אין היסטוריה עדיין."
        lines = []
        for item in history[:10]:  # last 10 interactions
            direction = "משתמש" if item.direction == "inbound" else "בוט"
            lines.append(f"{direction}: {item.message_text or ''}")
        return "\n".join(lines)
