# nutrition-bot — Project Rules

## Stack
- Backend: Python 3.11 + FastAPI + SQLAlchemy 2.0 async (asyncpg)
- AI: Claude Opus 4.6 (`claude-opus-4-6`) — all agents, all calls
- Telegram: python-telegram-bot v21 (webhook mode, no polling)
- DB: PostgreSQL via Supabase (connection string in env)
- Dashboard: Next.js 14 App Router + TypeScript + Tailwind (RTL Hebrew)
- Hosting: Railway (backend + dashboard as separate services)
- Scheduler: APScheduler AsyncIOScheduler

## Architecture
See `Specs_MD/ARCHITECTURE.md` for full agent map.

7 agents total:
- Business: Orchestrator, Nutrition, Motivation, Habits
- Operational (MVP = reporting only): Security, Performance, QA

## Critical Rules
- NEVER mention calories, weight, BMI to the user — ever
- NEVER recommend diets or restrictions
- Distress detection is mandatory — see `agents/orchestrator.py`
- All user-facing text in Hebrew, casual tone, with emojis
- All API keys in `.env` only, never in code
- User is a minor (age 14-18) — maximum care with data

## File Layout
```
backend/
  config.py          — Pydantic settings (single source of truth)
  main.py            — FastAPI app + webhook + dashboard API
  database/
    models.py        — SQLAlchemy models (users, meals, daily_scores, interactions)
    connection.py    — Async engine + session factory
  agents/
    base_agent.py    — BaseAgent: Claude calls with prompt caching
    onboarding.py    — Conversational onboarding (collects user profile)
    orchestrator.py  — Routes messages, distress guard, daily messages
    nutrition.py     — Meal analysis (text + Vision)
    motivation.py    — Emotional support + distress detection
    habits.py        — Streaks, Health Score, water tracking
  bot/
    app.py           — PTB Application builder
    handlers.py      — Telegram update handlers
  scheduler/
    jobs.py          — Daily messages (morning/lunch/evening) + operational agents
dashboard/
  src/app/           — Next.js App Router pages
  src/components/    — UI components
  src/lib/api.ts     — FastAPI client
```

## Spec Reference
- Functional spec: `nutrition_app_spec_v2.pdf` (original)
- Architecture: `Specs_MD/ARCHITECTURE.md`
- Changelog: `Specs_MD/CHANGELOG.md`
