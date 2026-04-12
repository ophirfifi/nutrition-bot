"""
OnboardingAgent — drives the first-contact questionnaire via a natural
Claude conversation. Collects the full user profile and returns structured
JSON when complete.
"""
import json
import logging

from agents.base_agent import BaseAgent
from database.models import UserModel
from database.repositories import users as user_repo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """אתה "נוטרי" — בוט תזונה חכם ואישי לנוער.
אתה מנהל שיחת היכרות עם משתמש חדש. המטרה שלך היא לאסוף מידע חיוני בשיחה טבעית, קלילה, ולא כמו שאלון משעמם.

מידע שעליך לאסוף (בסדר הגיוני, שאלה אחת בכל פעם):
1. שם פרטי
2. גיל (14–18 בלבד)
3. גובה (סנטימטרים)
4. סוג הספורט העיקרי
5. כמה פעמים בשבוע מתאמן/מת
6. עצימות אימון: קלה / בינונית / אינטנסיבית
7. כמה ארוחות ביום בדרך כלל
8. שעות אכילה עיקריות (בוקר/צהריים/ערב + נשנושים)
9. מאכלים שאוהב
10. מאכלים שלא אוהב / אלרגיות
11. מתי בא לך מתוק או נשנוש (אחרי אימון? לפני שינה?)
12. מתי הכי רעב ביום

כללים:
- שאל שאלה אחת בכל תגובה, הגב על מה שנאמר לפני כן
- שפה עברית קלילה, עם אמוג'ים
- אל תזכיר משקל, קלוריות, BMI — לעולם
- אל תתחיל כל תגובה עם "נהדר!" — תשתנה
- אם התשובה לא ברורה — שאל בנעימות לפרט

כשאספת את כל 12 הנקודות, החזר **אך ורק** אובייקט JSON תקין, ללא טקסט נוסף לפניו או אחריו:
{
  "complete": true,
  "data": {
    "name": "string",
    "age": number,
    "height": number,
    "sport_type": "string",
    "sport_frequency": number,
    "eating_habits": {
      "meals_per_day": number,
      "eating_times": ["HH:MM", ...]
    },
    "preferences": {
      "likes": ["string", ...],
      "dislikes": ["string", ...],
      "allergies": ["string", ...]
    },
    "triggers": {
      "sweet_cravings": "string",
      "hungriest_time": "string"
    }
  }
}

אם עדיין חסר מידע — המשך את השיחה ואל תחזיר JSON.
"""

COMPLETION_MESSAGE = """{name} 🎉 מעולה! עכשיו אני מכיר אותך טוב.

בניתי לך תוכנית גמישה שמתאימה בדיוק לך ול{sport} שלך 💪

מעכשיו:
📸 שלח לי תמונות של הארוחות שלך ואני אתן פידבק
💬 כתוב לי חופשי — על מה שאכלת, איך אתה מרגיש
⏰ אשלח לך 3 הודעות קצרות ביום

בהצלחה! 🚀"""


class OnboardingAgent(BaseAgent):

    async def process(self, user: UserModel, user_message: str) -> str:
        """
        Process one turn of onboarding conversation.
        Returns either the next question (str) or triggers profile save.
        """
        # Save user message to history
        await user_repo.save_onboarding_message(user.telegram_id, "user", user_message)

        # Rebuild history from stored messages
        history = list(user.onboarding_messages or [])
        history.append({"role": "user", "content": user_message})

        response_text = await self.call_claude(
            system=SYSTEM_PROMPT,
            messages=history,
            max_tokens=1024,
        )

        # Check if Claude returned a completion JSON
        try:
            data = json.loads(response_text.strip())
            if data.get("complete") is True:
                await self._save_profile(user.telegram_id, data["data"])
                sport = data["data"].get("sport_type", "ספורט")
                name = data["data"].get("name", "חבר")
                return COMPLETION_MESSAGE.format(name=name, sport=sport)
        except (json.JSONDecodeError, KeyError):
            pass  # not JSON — normal conversation turn

        # Save assistant response to history
        await user_repo.save_onboarding_message(user.telegram_id, "assistant", response_text)
        return response_text

    async def _save_profile(self, telegram_id: int, data: dict) -> None:
        profile_fields = {
            "name": data.get("name"),
            "age": data.get("age"),
            "height": data.get("height"),
            "sport_type": data.get("sport_type"),
            "sport_frequency": data.get("sport_frequency"),
            "eating_habits": data.get("eating_habits"),
            "preferences": data.get("preferences"),
            "triggers": data.get("triggers"),
        }
        await user_repo.complete_onboarding(telegram_id, profile_fields)
        logger.info("Onboarding complete for user %s", telegram_id)

    async def get_welcome_message(self) -> str:
        return (
            "שלום! 👋 אני נוטרי — הבוט שיעזור לך לאכול טוב ולהרגיש מעולה.\n\n"
            "כדי להתאים לך תוכנית אישית, בוא נכיר קצת.\n"
            "ראשית — איך קוראים לך? 😊"
        )
