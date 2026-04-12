# Architecture — Smart Nutrition Bot

## System Overview

```
Telegram User
     │
     ▼ HTTP POST
┌─────────────────────────────────────────────┐
│  FastAPI Backend (Railway)                  │
│  /webhook/{secret}                          │
│       │                                     │
│       ▼                                     │
│  bot/handlers.py                            │
│       │                                     │
│  ┌────┴────────────────────────────────┐   │
│  │ onboarding_complete?                │   │
│  │   NO → OnboardingAgent (Claude)     │   │
│  │   YES → OrchestratorAgent (Claude)  │   │
│  └────┬────────────────────────────────┘   │
│       │                                     │
│       ├── NutritionAgent  (Claude Vision)   │
│       ├── MotivationAgent (Claude)          │
│       └── HabitsAgent     (Claude)          │
│                                             │
│  APScheduler (daily messages × 3)          │
│  ┌────────────────────────────────────┐    │
│  │  08:00 morning_message             │    │
│  │  13:00 lunch_message               │    │
│  │  20:00 evening_message             │    │
│  │  00:00 calculate_daily_scores      │    │
│  └────────────────────────────────────┘    │
│                                             │
│  REST API /api/*  ◄─── Next.js Dashboard   │
└─────────────────────────────────────────────┘
     │
     ▼
PostgreSQL (Supabase)
  users / meals / daily_scores / interactions
```

## Agent Responsibilities

| Agent | Trigger | Claude Calls |
|-------|---------|-------------|
| OnboardingAgent | `/start` or new user text | 1 per turn (conversational) |
| OrchestratorAgent | Every user message | 1 (routes) + optional sub-agent |
| NutritionAgent | Photo OR food-related text | 1 (Vision-capable) |
| MotivationAgent | Emotional/motivational text | 1 |
| HabitsAgent | Habits/water/streak queries | 1 |

## Distress Detection (Critical — minor user)

1. Keyword scan (sync, before any Claude call)
2. If triggered: stop interaction, send safety message + professional referral
3. Set `interactions.distress_flag = true`
4. Distress flag visible in admin dashboard

## Health Score Formula (0–100, daily)

| Parameter | Weight | Signal |
|-----------|--------|--------|
| Meal adherence | 30% | meals logged vs. recommended |
| Nutritional variety | 25% | food group coverage |
| Water intake | 20% | glasses reported |
| Junk avoidance | 15% | junk vs. total meals |
| Reporting consistency | 10% | messages + photos sent |

## Data Flow — Photo Analysis

```
User sends photo
  → handlers.py downloads via Telegram file API
  → converts to base64 (JPEG)
  → NutritionAgent.analyze_meal(photo_base64, media_type)
  → Claude Opus 4.6 Vision
  → {rating, categories, feedback, recommendations}
  → saved to meals table
  → response sent to user
```

## Environment Variables
See `.env.example` for full list.

## Prompt Caching
All system prompts use `cache_control: {type: "ephemeral"}` to reduce token costs across repeated agent calls (5-min TTL in Claude's cache).
