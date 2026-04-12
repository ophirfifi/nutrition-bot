"""
Pydantic models that mirror Firestore document structures.
Firestore collections layout:
  users/{telegram_id}
  users/{telegram_id}/meals/{meal_id}
  users/{telegram_id}/daily_scores/{YYYY-MM-DD}
  users/{telegram_id}/interactions/{interaction_id}
"""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    telegram_id: int
    name: Optional[str] = None
    age: Optional[int] = None
    height: Optional[int] = None          # cm
    sport_type: Optional[str] = None
    sport_frequency: Optional[int] = None  # times per week
    eating_habits: Optional[dict] = None   # {meals_per_day, eating_times}
    preferences: Optional[dict] = None    # {likes, dislikes, allergies}
    triggers: Optional[dict] = None       # {sweet_cravings, hungriest_time}
    onboarding_complete: bool = False
    # [{role: "user"|"assistant", content: "..."}]
    onboarding_messages: list = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_firestore(self) -> dict:
        data = self.model_dump()
        data["created_at"] = self.created_at
        data["updated_at"] = self.updated_at
        return data


class MealModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: Optional[str] = None             # breakfast/lunch/dinner/snack
    image_url: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[dict] = None     # {protein, carbs, fat, vegetables}
    rating: Optional[str] = None          # green/yellow/red
    score: Optional[int] = None           # 0-100
    feedback_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_firestore(self) -> dict:
        data = self.model_dump(exclude={"id", "telegram_id"})
        data["timestamp"] = self.timestamp
        data["created_at"] = self.created_at
        return data


class DailyScoreModel(BaseModel):
    telegram_id: int
    date: str  # "YYYY-MM-DD"
    health_score: int = 0
    meals_count: int = 0
    water_intake: int = 0    # glasses
    junk_count: int = 0
    balance_score: int = 0
    streak_days: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_firestore(self) -> dict:
        data = self.model_dump(exclude={"telegram_id"})
        data["created_at"] = self.created_at
        return data


class InteractionModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    telegram_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_type: Optional[str] = None      # nutrition/motivation/habits/orchestrator/onboarding
    direction: str = "inbound"            # inbound/outbound
    message_text: Optional[str] = None
    message_type: str = "text"            # text/image/system
    distress_flag: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_firestore(self) -> dict:
        data = self.model_dump(exclude={"id", "telegram_id"})
        data["timestamp"] = self.timestamp
        data["created_at"] = self.created_at
        return data
