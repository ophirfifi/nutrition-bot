"""
Firestore repository layer — all DB operations go through these classes.
Collection structure:
  users/{telegram_id}                          → UserModel
  users/{telegram_id}/meals/{meal_id}          → MealModel
  users/{telegram_id}/daily_scores/{YYYY-MM-DD}→ DailyScoreModel
  users/{telegram_id}/interactions/{id}        → InteractionModel
"""
import logging
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from database.connection import get_db
from database.models import DailyScoreModel, InteractionModel, MealModel, UserModel

logger = logging.getLogger(__name__)

MIN_HEALTHY_SCORE = 40  # threshold to count a day in the streak


# ── User ──────────────────────────────────────────────────────────────────────

class UserRepository:
    @staticmethod
    def _ref(telegram_id: int):
        return get_db().collection("users").document(str(telegram_id))

    async def get(self, telegram_id: int) -> Optional[UserModel]:
        doc = await self._ref(telegram_id).get()
        if not doc.exists:
            return None
        return UserModel(**doc.to_dict())

    async def create(self, telegram_id: int) -> UserModel:
        user = UserModel(telegram_id=telegram_id)
        await self._ref(telegram_id).set(user.to_firestore())
        logger.info("Created user %s", telegram_id)
        return user

    async def get_or_create(self, telegram_id: int) -> tuple[UserModel, bool]:
        """Returns (user, created). created=True if new user."""
        user = await self.get(telegram_id)
        if user:
            return user, False
        return await self.create(telegram_id), True

    async def update(self, telegram_id: int, **fields) -> None:
        fields["updated_at"] = datetime.utcnow()
        await self._ref(telegram_id).update(fields)

    async def save_onboarding_message(self, telegram_id: int, role: str, content: str) -> None:
        """Appends a message to the onboarding conversation history."""
        from google.cloud.firestore_v1 import ArrayUnion
        await self._ref(telegram_id).update({
            "onboarding_messages": ArrayUnion([{"role": role, "content": content}]),
            "updated_at": datetime.utcnow(),
        })

    async def complete_onboarding(self, telegram_id: int, profile_data: dict) -> None:
        await self._ref(telegram_id).update({
            **profile_data,
            "onboarding_complete": True,
            "onboarding_messages": [],  # clear to save space
            "updated_at": datetime.utcnow(),
        })


# ── Meals ─────────────────────────────────────────────────────────────────────

class MealRepository:
    @staticmethod
    def _col(telegram_id: int):
        return get_db().collection("users").document(str(telegram_id)).collection("meals")

    async def create(self, meal: MealModel) -> MealModel:
        await self._col(meal.telegram_id).document(meal.id).set(meal.to_firestore())
        return meal

    async def get_today(self, telegram_id: int) -> list[MealModel]:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        docs = (
            self._col(telegram_id)
            .where("timestamp", ">=", today_start)
            .order_by("timestamp", direction="DESCENDING")
        )
        results = []
        async for doc in docs.stream():
            results.append(MealModel(id=doc.id, telegram_id=telegram_id, **doc.to_dict()))
        return results

    async def get_recent(self, telegram_id: int, limit: int = 10) -> list[MealModel]:
        docs = (
            self._col(telegram_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )
        results = []
        async for doc in docs.stream():
            results.append(MealModel(id=doc.id, telegram_id=telegram_id, **doc.to_dict()))
        return results

    async def count_today_junk(self, telegram_id: int) -> int:
        meals = await self.get_today(telegram_id)
        return sum(1 for m in meals if m.rating == "red")


# ── Daily Scores ──────────────────────────────────────────────────────────────

class DailyScoreRepository:
    @staticmethod
    def _ref(telegram_id: int, date_str: str):
        return (
            get_db()
            .collection("users")
            .document(str(telegram_id))
            .collection("daily_scores")
            .document(date_str)
        )

    async def upsert(self, score: DailyScoreModel) -> None:
        await self._ref(score.telegram_id, score.date).set(score.to_firestore(), merge=True)

    async def get(self, telegram_id: int, date_str: str) -> Optional[DailyScoreModel]:
        doc = await self._ref(telegram_id, date_str).get()
        if not doc.exists:
            return None
        return DailyScoreModel(telegram_id=telegram_id, **doc.to_dict())

    async def get_history(self, telegram_id: int, days: int = 30) -> list[DailyScoreModel]:
        cutoff = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        col = (
            get_db()
            .collection("users")
            .document(str(telegram_id))
            .collection("daily_scores")
            .where("date", ">=", cutoff)
            .order_by("date", direction="ASCENDING")
        )
        results = []
        async for doc in col.stream():
            results.append(DailyScoreModel(telegram_id=telegram_id, **doc.to_dict()))
        return results

    async def calculate_streak(self, telegram_id: int) -> int:
        """Count consecutive days ending today where health_score >= MIN_HEALTHY_SCORE."""
        streak = 0
        check_date = datetime.utcnow().date()
        while True:
            score_doc = await self.get(telegram_id, check_date.isoformat())
            if score_doc and score_doc.health_score >= MIN_HEALTHY_SCORE:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        return streak


# ── Interactions ──────────────────────────────────────────────────────────────

class InteractionRepository:
    @staticmethod
    def _col(telegram_id: int):
        return (
            get_db()
            .collection("users")
            .document(str(telegram_id))
            .collection("interactions")
        )

    async def log(self, interaction: InteractionModel) -> None:
        await self._col(interaction.telegram_id).document(interaction.id).set(
            interaction.to_firestore()
        )

    async def get_recent(self, telegram_id: int, limit: int = 20) -> list[InteractionModel]:
        docs = (
            self._col(telegram_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(limit)
        )
        results = []
        async for doc in docs.stream():
            results.append(InteractionModel(id=doc.id, telegram_id=telegram_id, **doc.to_dict()))
        return results


# ── Admin (cross-user queries) ───────────────────────────────────────────────

class AdminRepository:

    async def overview(self) -> dict:
        db = get_db()
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Total users
        total_users = 0
        async for _ in db.collection("users").stream():
            total_users += 1

        # Active today (users updated today)
        active_today = 0
        async for doc in db.collection("users").where("updated_at", ">=", today_start).stream():
            active_today += 1

        # Meals today (collection group query)
        meals_today = 0
        async for _ in db.collection_group("meals").where("timestamp", ">=", today_start).stream():
            meals_today += 1

        # Distress today (collection group query)
        distress_today = 0
        async for _ in (
            db.collection_group("interactions")
            .where("distress_flag", "==", True)
            .where("timestamp", ">=", today_start)
            .stream()
        ):
            distress_today += 1

        return {
            "total_users": total_users,
            "active_today": active_today,
            "meals_today": meals_today,
            "distress_today": distress_today,
        }

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[dict]:
        db = get_db()
        query = db.collection("users").order_by("updated_at", direction="DESCENDING")
        results = []
        idx = 0
        async for doc in query.stream():
            if idx < offset:
                idx += 1
                continue
            if len(results) >= limit:
                break
            data = doc.to_dict()
            # Get today's score
            today_str = datetime.utcnow().date().isoformat()
            score_doc = await (
                db.collection("users")
                .document(doc.id)
                .collection("daily_scores")
                .document(today_str)
                .get()
            )
            health_score = score_doc.to_dict().get("health_score", 0) if score_doc.exists else 0

            results.append({
                "telegram_id": int(doc.id),
                "name": data.get("name"),
                "age": data.get("age"),
                "sport_type": data.get("sport_type"),
                "onboarding_complete": data.get("onboarding_complete", False),
                "health_score": health_score,
                "updated_at": data.get("updated_at").isoformat() if data.get("updated_at") else None,
                "created_at": data.get("created_at").isoformat() if data.get("created_at") else None,
            })
            idx += 1
        return results

    async def user_detail(self, telegram_id: int) -> dict | None:
        db = get_db()
        user_doc = await db.collection("users").document(str(telegram_id)).get()
        if not user_doc.exists:
            return None
        user_data = user_doc.to_dict()

        # Recent meals
        meal_docs = (
            db.collection("users").document(str(telegram_id))
            .collection("meals")
            .order_by("timestamp", direction="DESCENDING")
            .limit(20)
        )
        meals_list = []
        async for doc in meal_docs.stream():
            m = doc.to_dict()
            m["id"] = doc.id
            meals_list.append(m)

        # Score history (last 30 days)
        cutoff = (datetime.utcnow() - timedelta(days=30)).date().isoformat()
        score_docs = (
            db.collection("users").document(str(telegram_id))
            .collection("daily_scores")
            .where("date", ">=", cutoff)
            .order_by("date", direction="ASCENDING")
        )
        scores_list = []
        async for doc in score_docs.stream():
            scores_list.append(doc.to_dict())

        # Recent interactions
        int_docs = (
            db.collection("users").document(str(telegram_id))
            .collection("interactions")
            .order_by("timestamp", direction="DESCENDING")
            .limit(50)
        )
        interactions_list = []
        async for doc in int_docs.stream():
            interactions_list.append(doc.to_dict())

        return {
            "user": {
                "telegram_id": telegram_id,
                "name": user_data.get("name"),
                "age": user_data.get("age"),
                "height": user_data.get("height"),
                "sport_type": user_data.get("sport_type"),
                "sport_frequency": user_data.get("sport_frequency"),
                "eating_habits": user_data.get("eating_habits"),
                "preferences": user_data.get("preferences"),
                "triggers": user_data.get("triggers"),
                "onboarding_complete": user_data.get("onboarding_complete", False),
                "created_at": user_data.get("created_at").isoformat() if user_data.get("created_at") else None,
            },
            "meals": meals_list,
            "scores": scores_list,
            "interactions": interactions_list,
        }

    async def recent_interactions(self, limit: int = 50, distress_only: bool = False) -> list[dict]:
        db = get_db()
        query = db.collection_group("interactions")
        if distress_only:
            query = query.where("distress_flag", "==", True)
        query = query.order_by("timestamp", direction="DESCENDING").limit(limit)

        # Build a name cache to avoid repeated lookups
        name_cache: dict[str, str | None] = {}
        results = []
        async for doc in query.stream():
            data = doc.to_dict()
            tid = doc.reference.parent.parent.id
            if tid not in name_cache:
                user_doc = await db.collection("users").document(tid).get()
                name_cache[tid] = user_doc.to_dict().get("name") if user_doc.exists else None
            data["telegram_id"] = int(tid)
            data["user_name"] = name_cache[tid]
            results.append(data)
        return results


# ── Singletons ────────────────────────────────────────────────────────────────
users = UserRepository()
meals = MealRepository()
scores = DailyScoreRepository()
interactions = InteractionRepository()
admin = AdminRepository()
