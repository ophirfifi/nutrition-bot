# Changelog

## [0.2.0] — 2026-04-13 — Railway Deployment & Production Setup

### Added
- Railway deployment for backend (FastAPI) and dashboard (Next.js)
- SKIP_TELEGRAM flag for local dev when corporate VPN blocks Telegram API
- Firebase credentials base64 encoding for production (FIREBASE_CREDENTIALS_BASE64)
- Next.js standalone output mode for containerized deploys
- Railway healthcheck configuration for both services

### Fixed
- Next.js standalone server binding to 0.0.0.0 (was localhost, blocked Railway healthcheck)
- Upgraded next from 14.2.18 to ^14.2.35 (CVE-2025-55184, CVE-2025-67779)
- Forced NIXPACKS builder (Railway default RAILPACK was inconsistent)

### Infrastructure
- Backend: https://backend-production-1185.up.railway.app
- Dashboard: https://dashboard-production-09c0.up.railway.app
- GitHub repo: ophirfifi/nutrition-bot (master branch, auto-deploy)
- Environment variables configured via Railway API

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
