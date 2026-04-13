"""
NutritionAgent — analyzes meals from photos (Claude Vision) or text.
Returns a human-readable Hebrew response + saves meal to Firestore.
"""
import json
import logging
import uuid
from datetime import datetime

from agents.base_agent import BaseAgent
from database.models import MealModel, UserModel
from database.repositories import meals as meal_repo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה סוכן תזונה באפליקציית תזונה חכמה לנוער בשם "נוטרי".

תפקידך:
- לנתח ארוחות מתמונות ומטקסט
- לדרג ארוחות (ירוק/צהוב/אדום)
- להפיק המלצות מותאמות אישית

פרופיל המשתמש:
{user_profile}

כללים קשיחים:
- דבר בעברית בלבד
- טון קליל כמו חבר, עם אמוג'ים
- אף פעם לא להזכיר קלוריות, משקל, BMI
- אף פעם לא להמליץ על דיאטה או הגבלה
- חיובי ולא שיפוטי — תמיד
- התאם לספורט של המשתמש: כדורסל/ספורט אינטנסיבי = צריך יותר פחמימות וחלבון

דרוג:
🟢 ירוק = ארוחה מאוזנת עם כמה קבוצות מזון
🟡 צהוב = בסדר, יש מקום לשיפור קטן
🔴 אדום = ג׳אנק / חסר איזון (אבל לגמרי בסדר מדי פעם!)

דוגמאות לטון:
❌ "ג׳אנק פוד — לא בריא"
✅ "😅 פחות אידיאלי, אבל לגמרי סבבה מדי פעם"

❌ "לא אכלת ירקות"
✅ "🥗 כדאי להוסיף ירק בצד — קצת צבע לצלחת!"

❌ "ארוחה לא מאוזנת"
✅ "🟡 יש כאן פחמימות טובות, רק חסר קצת חלבון — הוסף ביצה או טונה!"

החזר **אך ורק** JSON תקין, ללא טקסט נוסף:
{
  "rating": "green" | "yellow" | "red",
  "categories": {
    "protein": true/false,
    "carbs": true/false,
    "fat": true/false,
    "vegetables": true/false
  },
  "feedback": "הודעה קצרה וחיובית למשתמש (1-2 משפטים)",
  "recommendations": "המלצה אחת קצרה לשיפור (לא חובה, יכול להיות null)"
}
"""

RATING_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


class NutritionAgent(BaseAgent):

    async def analyze_meal(
        self,
        user: UserModel,
        text_description: str | None = None,
        photo_base64: str | None = None,
        media_type: str = "image/jpeg",
    ) -> str:
        system = SYSTEM_PROMPT.format(user_profile=self._format_profile(user))

        if photo_base64:
            prompt = text_description or "תנתח את הארוחה בתמונה."
            raw = await self.call_claude_vision(
                system=system,
                photo_base64=photo_base64,
                media_type=media_type,
                text_prompt=prompt,
            )
        else:
            messages = [{"role": "user", "content": text_description or "מה אכלתי?"}]
            raw = await self.call_claude(system=system, messages=messages)

        try:
            data = json.loads(self._strip_codeblock(raw))
            return await self._build_response(user, data, text_description)
        except (json.JSONDecodeError, KeyError):
            logger.warning("NutritionAgent returned non-JSON: %.200s", raw)
            return raw

    async def _build_response(
        self, user: UserModel, data: dict, description: str | None
    ) -> str:
        rating = data.get("rating", "yellow")
        emoji = RATING_EMOJI.get(rating, "🟡")
        feedback = data.get("feedback", "")
        recommendation = data.get("recommendations")

        response = f"{emoji} {feedback}"
        if recommendation:
            response += f"\n\n💡 {recommendation}"

        # Persist meal to Firestore
        try:
            meal = MealModel(
                id=str(uuid.uuid4()),
                telegram_id=user.telegram_id,
                timestamp=datetime.utcnow(),
                description=description,
                categories=data.get("categories"),
                rating=rating,
                feedback_text=feedback,
            )
            await meal_repo.create(meal)
        except Exception as exc:
            logger.error("Failed to save meal for user %s: %s", user.telegram_id, exc, exc_info=True)

        return response

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
    def _format_profile(user: UserModel) -> str:
        return json.dumps(
            {
                "name": user.name,
                "age": user.age,
                "sport_type": user.sport_type,
                "sport_frequency": user.sport_frequency,
                "preferences": user.preferences,
            },
            ensure_ascii=False,
        )
