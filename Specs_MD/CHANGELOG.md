# Changelog

## [0.1.0] — 2026-04-12 — Initial MVP Build

### Added
- Project scaffold: FastAPI backend + Next.js dashboard
- Database layer: users, meals, daily_scores, interactions tables (SQLAlchemy async)
- 5 AI agents: OnboardingAgent, OrchestratorAgent, NutritionAgent, MotivationAgent, HabitsAgent
- Telegram Bot webhook integration (python-telegram-bot v21)
- Conversational onboarding via Claude (natural questionnaire, extracts structured profile)
- Meal photo analysis using Claude Opus 4.6 Vision API
- Meal rating system (green / yellow / red)
- Distress detection with keyword scan + professional referral
- Daily Health Score calculation (0–100) with 5-parameter formula
- Streak tracking (consecutive balanced days)
- APScheduler: 3 daily proactive messages (morning / lunch / evening)
- Next.js dashboard: Hebrew RTL, dark theme, Health Score gauge, trend chart, streak, meals log, achievements
- Dashboard REST API endpoints: /api/dashboard, /api/health-history, /api/meals
- Prompt caching on all agent system prompts
- Railway deployment config
