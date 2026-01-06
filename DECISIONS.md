# ALPHA MACHINE - ARCHITECTURAL DECISIONS LOG
## Technical Choices & Rationale

**Purpose:** Document why we made specific technical decisions  
**Updated By:** Claude Code (whenever non-obvious choice is made)  
**Format:** ADR-style (Architecture Decision Record)

---

## How to Use This Document

**When to add an entry:**
- Choosing between 2+ viable technical options
- Deviating from BUILD_SPEC.md
- Making trade-offs (performance vs simplicity, cost vs features)
- Incurring technical debt intentionally
- Selecting libraries/frameworks

**When NOT to add an entry:**
- Following BUILD_SPEC.md exactly as written
- Obvious/standard choices (e.g., using FastAPI because spec says so)

---

## Decision Index

1. [Database: PostgreSQL over SQLite](#decision-1-postgresql-over-sqlite)
2. [Data Source: Polygon.io as primary](#decision-2-polygonio-primary)
3. [AI Framework: OpenAI + Anthropic + Google](#decision-3-multi-vendor-ai)
4. [psycopg3 over psycopg2](#decision-4-psycopg3-over-psycopg2)
5. [Flexible package versions](#decision-5-flexible-package-versions)
6. [Keyword-based sentiment analysis](#decision-6-keyword-based-sentiment)
7. [Reddit/News sentiment weighting](#decision-7-sentiment-weighting)
8. [Circuit Breaker for API resilience](#decision-8-circuit-breaker)
9. [Rule-based agent as baseline](#decision-9-rule-based-baseline)
10. [Weighted consensus algorithm](#decision-10-weighted-consensus)
11. [Reddit integration postponed](#decision-11-reddit-postponed)
12. [Railway + Vercel Deployment](#decision-12-railway-vercel-deployment)
13. [Celery Beat Worker Deployment](#decision-13-celery-beat-worker-deployment-strategy)
14. [Backtest Engine Architecture](#decision-14-backtest-engine-architecture)
15. [Telegram Bot Architecture](#decision-15-telegram-bot-architecture)
16. [Signal Threshold Adjustment](#decision-16-signal-threshold-adjustment)
17. [Example Decision Template](#decision-template)

---

## Decision 1: PostgreSQL over SQLite

**Date:** [YYYY-MM-DD - Claude Code: Fill this in]  
**Status:** ✅ Accepted | ⏳ Proposed | ❌ Rejected | 🔄 Superseded  
**Deciders:** Claude Code, User  
**Tags:** `database`, `infrastructure`, `milestone-1`

### Context

Need to choose database for storing signals, portfolio, market data.

BUILD_SPEC.md specifies PostgreSQL, but for a personal project, SQLite could work.

### Options Considered

#### Option A: PostgreSQL (Chosen ✅)
**Pros:**
- Production-grade, scales if needed
- Better concurrent access (Celery tasks)
- Advanced features (JSONB, full-text search)
- As specified in BUILD_SPEC.md

**Cons:**
- More complex setup (Docker required)
- Overkill for single user initially
- ~$10/mo cost when deployed (Railway)

#### Option B: SQLite
**Pros:**
- Zero setup, file-based
- Perfect for MVP/prototyping
- Free forever
- Faster for small datasets

**Cons:**
- No concurrent writes (Celery would fail)
- Doesn't scale
- Migration to Postgres later = painful

### Decision

**Chose: PostgreSQL (Option A)**

**Rationale:**
1. BUILD_SPEC.md already designed for PostgreSQL
2. Celery scheduled tasks need concurrent DB access
3. Starting with production DB = no migration later
4. Docker makes setup easy enough
5. $10/mo on Railway acceptable for final system

### Consequences

**Positive:**
- No future migration needed
- Can scale if portfolio grows
- Proper multi-agent concurrent access

**Negative:**
- Slightly more complex local dev setup
- Need Docker running always

**Technical Debt:** None

**Reversible:** No (once in production)

---

## Decision 2: Polygon.io as Primary Data Source

**Date:** [YYYY-MM-DD]  
**Status:** ✅ Accepted  
**Tags:** `data-pipeline`, `api`, `milestone-2`

### Context

Need real-time stock prices. Multiple free APIs available:
- Polygon.io (5 calls/min free)
- Finnhub (60 calls/min free)
- Alpha Vantage (25 calls/day)
- Yahoo Finance (unlimited, unofficial)

### Options Considered

#### Option A: Polygon.io (Chosen ✅)
- Free tier: 5 calls/min, delayed data
- Clean REST API
- Good documentation
- Upgrade path to real-time ($29/mo)

#### Option B: Yahoo Finance (yfinance)
- Unlimited free (unofficial API)
- 15-20min delay
- No rate limits
- Risk: Could break anytime (not official)

#### Option C: Finnhub
- 60 calls/min free
- Real-time API
- More generous limits

### Decision

**Chose: Polygon.io as primary, Finnhub as fallback**

**Rationale:**
1. BUILD_SPEC.md uses Polygon.io
2. 5 calls/min sufficient for 10 stocks (monitor every 5 min)
3. Official API = reliable
4. Fallback to Finnhub if Polygon fails
5. Yahoo Finance as last resort (cached data)

### Consequences

**Positive:**
- Reliable, official API
- Clear upgrade path
- Multi-source redundancy

**Negative:**
- 5 calls/min limit (need to batch requests)
- Delayed data on free tier (15min)

**Mitigation:**
- Cache aggressively
- Batch fetch all 10 stocks in one loop
- Use Finnhub fallback automatically

**Technical Debt:** None

---

## Decision 3: Multi-Vendor AI (OpenAI + Anthropic + Google)

**Date:** [YYYY-MM-DD]  
**Status:** ✅ Accepted  
**Tags:** `ai-agents`, `cost`, `milestone-3`

### Context

Need 4 AI agents for multi-perspective analysis.

Could use all from one vendor (e.g., 4x GPT-4) or mix vendors.

### Options Considered

#### Option A: All OpenAI (4x GPT-4)
- Cost: ~$80-120/mo
- Pros: Consistent API, easier
- Cons: Single point of failure, expensive

#### Option B: Multi-vendor mix (Chosen ✅)
- GPT-4 (contrarian) + Claude (growth) + Gemini (multi-modal) + LSTM (predictor)
- Cost: ~$40-60/mo (Gemini free, LSTM free)
- Pros: Diverse perspectives, redundancy, cheaper
- Cons: 3 different APIs to manage

### Decision

**Chose: Multi-vendor (Option B)**

**Rationale:**
1. Different AI models = truly different perspectives
2. Cost savings: Gemini free, reduces OpenAI usage
3. Reduces vendor lock-in
4. BUILD_SPEC.md designed for multi-agent diversity
5. Each model has strengths: GPT-4 (reasoning), Claude (balanced), Gemini (multi-modal)

### Consequences

**Positive:**
- Better consensus algorithm (truly independent views)
- Cost: $40-60/mo vs $80-120/mo
- No single vendor dependency

**Negative:**
- 3 API integrations instead of 1
- Different error handling per vendor
- Slightly more complex code

**Mitigation:**
- Abstract agent interface (base_agent.py)
- Graceful fallback if one API fails

**Technical Debt:** None (good abstraction)

---

## Decision 4: psycopg3 over psycopg2

**Date:** 2025-12-20
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `database`, `python`, `milestone-1`

### Context

BUILD_SPEC.md specified `psycopg2-binary==2.9.9`, but this failed to install on Python 3.13 due to C API changes.

### Options Considered

#### Option A: Downgrade Python to 3.11/3.12
- Would work with psycopg2
- Cons: Older Python, less future-proof

#### Option B: Use psycopg3 (Chosen ✅)
- Native async support
- Better Python 3.13 compatibility
- Modern API

### Decision

**Chose: psycopg3 (Option B)**

**Rationale:**
1. psycopg3 is the modern successor to psycopg2
2. Better Python 3.13+ compatibility
3. No need to downgrade Python
4. SQLAlchemy supports both with minimal config change

### Consequences

**Positive:**
- Works with Python 3.13
- Future-proof choice
- Native async support available

**Negative:**
- Required dialect change in database.py (`postgresql+psycopg://`)

**Technical Debt:** None

---

## Decision 5: Flexible Package Versions

**Date:** 2025-12-20
**Status:** ✅ Accepted
**Tags:** `dependencies`, `python`, `milestone-1`

### Context

Multiple packages (pandas, numpy) failed to build on Python 3.13 with exact version pins from BUILD_SPEC.md.

### Decision

Changed all `==` version pins to `>=` minimum versions in requirements.txt.

**Rationale:**
1. Python 3.13 requires newer package versions
2. `>=` allows pip to resolve compatible versions
3. More maintainable long-term

### Consequences

**Positive:**
- All packages install successfully
- Automatic compatibility resolution

**Negative:**
- Slightly less reproducible builds (minor risk)

**Mitigation:**
- Can add `pip freeze > requirements.lock` for exact versions later

---

## Decision 6: Keyword-Based Sentiment Analysis

**Date:** 2025-12-21
**Status:** ✅ Accepted
**Tags:** `sentiment`, `nlp`, `milestone-2`

### Context

Need sentiment analysis for Reddit posts and news headlines. Options:
- Simple keyword matching
- Pre-trained models (FinBERT, VADER)
- Custom ML model

### Options Considered

#### Option A: Keyword-based (Chosen ✅)
- Simple positive/negative word lists
- Fast, no dependencies
- Works offline

#### Option B: FinBERT
- Financial domain-specific
- Better accuracy
- Requires transformers library (~2GB)

### Decision

**Chose: Keyword-based for MVP (Option A)**

**Rationale:**
1. Simple and fast for MVP
2. No additional heavy dependencies
3. Easy to understand and debug
4. Good enough for initial testing
5. FinBERT can be added in Milestone 3 as upgrade

### Consequences

**Positive:**
- Fast implementation
- No model loading time
- Easy to customize word lists

**Negative:**
- Less accurate than ML models
- Doesn't understand context

**Technical Debt:**
- Should upgrade to FinBERT in Milestone 3 for better accuracy
- Impact: Medium
- Plan: Add as optional enhancement

---

## Decision 7: Reddit/News Sentiment Weighting (60/40)

**Date:** 2025-12-21
**Status:** ✅ Accepted
**Tags:** `sentiment`, `algorithm`, `milestone-2`

### Context

Need to combine Reddit and News sentiment into single score. How to weight them?

### Options Considered

#### Option A: Equal weighting (50/50)
- Simple
- Treats both sources equally

#### Option B: Reddit-heavy (60/40) (Chosen ✅)
- Prioritizes retail investor sentiment
- r/wallstreetbets often leads price moves

#### Option C: News-heavy (40/60)
- Prioritizes institutional/professional view
- More "reliable" sources

### Decision

**Chose: 60% Reddit, 40% News (Option B)**

**Rationale:**
1. Alpha Machine targets AI/tech stocks popular with retail
2. r/wallstreetbets sentiment often precedes price moves
3. Retail sentiment more relevant for short-term signals
4. News often lags market moves
5. Can adjust weights based on backtesting results

### Consequences

**Positive:**
- Captures retail momentum early
- Aligned with target stock universe (AI/tech)

**Negative:**
- May miss institutional-driven moves
- Reddit can be noisy/manipulated

**Mitigation:**
- Weights are configurable in code
- Can A/B test different weightings later

**Technical Debt:** None

---

## Decision 8: Circuit Breaker for API Resilience

**Date:** 2025-12-21
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `reliability`, `api`, `foundation-hardening`

### Context

External APIs (Polygon, Finnhub, Reddit, NewsAPI) can fail or rate-limit. Need resilient error handling.

### Options Considered

#### Option A: Simple retry with fixed delay
- Easy to implement
- Cons: Can hammer failing API, doesn't prevent cascading failures

#### Option B: Retry with exponential backoff + Circuit Breaker (Chosen ✅)
- Exponential backoff prevents API hammering
- Circuit Breaker prevents repeated calls to failing services
- Industry standard pattern

### Decision

**Chose: Retry + Circuit Breaker (Option B)**

**Rationale:**
1. Exponential backoff respects API rate limits
2. Circuit Breaker prevents wasted calls when service is down
3. Automatic recovery when service comes back
4. Production-grade reliability pattern

### Consequences

**Positive:**
- Resilient to transient failures
- Prevents cascading failures
- Automatic recovery

**Negative:**
- Slightly more complex code

**Technical Debt:** None

---

## Decision 9: Rule-Based Agent as Baseline

**Date:** 2025-12-21
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `agents`, `architecture`, `foundation-hardening`

### Context

Need agent framework before implementing AI-powered agents. Should we start with AI agents directly or create a simpler baseline first?

### Options Considered

#### Option A: Start with AI agents (GPT-4, Claude)
- Full power immediately
- Cons: Complex, expensive to test, hard to debug

#### Option B: Rule-based agent first (Chosen ✅)
- Simple weighted scoring (RSI, momentum, sentiment)
- No API costs during testing
- Easy to understand and debug
- Foundation for AI agents

### Decision

**Chose: Rule-based baseline first (Option B)**

**Rationale:**
1. Can test full pipeline without AI API costs
2. Provides comparison baseline for AI agents
3. Simpler to debug and understand
4. Works offline/without API keys
5. Still useful in production as "fast" signal

### Consequences

**Positive:**
- Free testing of signal pipeline
- Baseline for measuring AI agent value
- Works immediately without AI API keys

**Negative:**
- Less sophisticated than AI agents

**Technical Debt:** None (intentional design)

---

## Decision 10: Weighted Consensus Algorithm

**Date:** 2025-12-21
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `consensus`, `algorithm`, `foundation-hardening`

### Context

Multiple agents produce signals. Need algorithm to combine them into final recommendation.

### Options Considered

#### Option A: Simple majority vote
- Easy to implement
- Cons: Ignores confidence, all agents equal

#### Option B: Weighted voting by agent weight (Chosen ✅)
- Each agent has configurable weight
- Signals weighted by confidence
- Position sizing based on agreement

#### Option C: ML meta-model
- Train model on agent outputs
- Cons: Complex, needs training data

### Decision

**Chose: Weighted voting (Option B)**

**Rationale:**
1. Balances simplicity with sophistication
2. Agent weights allow tuning based on performance
3. Confidence weighting surfaces high-conviction signals
4. Agreement ratio informs position sizing
5. No training data needed

**Algorithm:**
- Combined weight = agent_weight × signal_confidence
- Weighted average score = Σ(score × weight) / Σ(weight)
- Position size based on confidence + agreement

### Consequences

**Positive:**
- Tunable per-agent influence
- Position sizing reflects conviction
- Interpretable decisions

**Negative:**
- Requires manual weight tuning initially

**Mitigation:**
- Can implement automatic weight adjustment based on agent performance

**Technical Debt:** None

---

## Decision 11: Reddit Integration Postponed

**Date:** 2025-12-21
**Status:** ⏳ Temporary
**Deciders:** User, Claude Code
**Tags:** `sentiment`, `api`, `milestone-2`

### Context

Reddit API (PRAW) requires OAuth credentials. User will provide Reddit API keys later.

### Decision

**Temporarily skip Reddit integration. Sentiment analysis uses NewsAPI only.**

**Current state:**
- NewsAPI: ✅ Working (30 articles, sentiment scoring)
- Reddit: ⏳ Skipped (credentials not configured)
- Combined sentiment: Uses 100% News (instead of 60/40 split)

### When Reddit Keys Are Available

1. Add to `backend/.env`:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   ```

2. Reddit sentiment will automatically activate

3. Combined sentiment will switch to:
   - 60% Reddit (r/wallstreetbets, r/stocks, r/investing)
   - 40% News

### Consequences

**Positive:**
- Can proceed with development without blocking
- NewsAPI provides sufficient sentiment for MVP testing
- Easy to enable Reddit when keys are ready

**Negative:**
- Missing retail investor sentiment (Reddit often leads price moves)
- Less accurate sentiment for meme stocks

**Technical Debt:**
- **REMINDER:** Reddit API keys still required for full functionality
- Impact: Medium (sentiment less accurate without Reddit)
- Plan: Add Reddit keys when available, no code changes needed

---

## Decision 12: Railway + Vercel Deployment

**Date:** 2026-01-04
**Status:** ✅ Accepted
**Deciders:** Claude Code, User
**Tags:** `deployment`, `infrastructure`, `milestone-6`

### Context

Need to deploy Alpha Machine to production. Multiple hosting options available:
- Railway (backend) + Vercel (frontend) - BUILD_SPEC.md recommendation
- AWS (ECS, RDS, ElastiCache) - enterprise grade
- Heroku - simple but expensive
- Self-hosted VPS - cheapest but most work

### Options Considered

#### Option A: Railway + Vercel (Chosen ✅)
**Pros:**
- Railway: Native PostgreSQL + Redis support, auto-deploy from GitHub
- Vercel: Excellent for React/Next.js, free tier generous
- Simple configuration (Procfile, vercel.json)
- Cost: ~$5-10/mo Railway + free Vercel

**Cons:**
- Railway CLI auth issues (used GraphQL API instead)
- Need separate services configuration

#### Option B: AWS (ECS + RDS + ElastiCache)
**Pros:**
- Enterprise-grade, highly scalable
- Full control

**Cons:**
- Expensive (~$50-100/mo minimum)
- Complex setup (VPC, security groups, IAM)
- Overkill for single-user system

### Decision

**Chose: Railway + Vercel (Option A)**

**Rationale:**
1. BUILD_SPEC.md recommended this stack
2. Auto-deploy from GitHub (push to main → deploy)
3. Managed PostgreSQL and Redis included
4. Cost effective (~$5-10/mo)
5. Simple configuration (Procfile + environment variables)

### Implementation Notes

**Railway setup:**
- Used Nixpacks builder (auto-detects Python)
- Procfile: `web: python scripts/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables set as shared variables in project
- Auto-deploy on push to main branch

**Vercel setup:**
- Connected to GitHub repo
- Auto-deploys frontend folder
- API proxy configured in vercel.json

**Issues Encountered:**
1. Dockerfile not found → switched to Nixpacks
2. Port binding hardcoded → fixed to use $PORT
3. Anthropic API credits → user added credits to account
4. Vercel authentication → user disabled team-level auth

### Consequences

**Positive:**
- Zero-downtime deployments
- Auto-scaling on Railway
- Git-based workflow
- Affordable for MVP

**Negative:**
- Railway CLI authentication issues (workaround: GraphQL API)
- Environment variables need manual setup per service

**Technical Debt:** None

**Cost:**
- Railway: ~$5/mo (hobby plan with PostgreSQL + Redis)
- Vercel: Free tier
- AI APIs: Variable (~$10-30/mo depending on usage)

---

## Decision 13: Celery Beat Worker Deployment Strategy

**Date:** 2026-01-04
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `celery`, `deployment`, `automation`, `post-mvp`

### Context

Need to deploy Celery Beat scheduler for automated signal generation. Railway already hosts the backend API. Key considerations:
- Celery workers don't serve HTTP (no port binding)
- Railway expects HTTP healthcheck by default
- Need to share environment variables with backend
- Worker should auto-restart on failure

### Options Considered

#### Option A: Separate Railway Service (Chosen ✅)
**Pros:**
- Independent scaling from API
- Isolated logs and monitoring
- Can restart worker without affecting API
- Clear separation of concerns

**Cons:**
- Needs separate configuration
- Environment variables duplicated
- Additional Railway resource

#### Option B: Same Service, Multiple Processes
**Pros:**
- Single deployment
- Shared env vars automatically
- Simpler management

**Cons:**
- Can't scale independently
- Worker crash might affect API
- Railway not designed for multi-process

#### Option C: Dedicated Beat + Worker Services (3 total)
**Pros:**
- Beat and worker fully isolated
- Fine-grained control

**Cons:**
- Overkill for current scale
- More complexity
- Higher cost

### Decision

**Chose: Separate Railway Service with Combined Worker+Beat (Option A)**

**Rationale:**
1. Worker service can fail without affecting API
2. Combined `--beat` flag keeps Beat and Worker in single process (simpler)
3. Railway GraphQL API allows fully automated deployment
4. Separate config file without healthcheck (worker doesn't serve HTTP)

### Implementation Notes

**Worker Service Configuration:**
```
Service ID: 2840fcc8-1b25-4526-9ba4-73e14e01e8e6
Start Command: celery -A app.tasks.celery_app worker --beat --loglevel=info --concurrency=2
Root Directory: backend
Config: Uses /railway.toml (root level, no healthcheck)
```

**Config File Strategy:**
- `/railway.toml` (root) - No healthcheck, for worker service
- `/backend/railway.toml` - With healthcheck, for API service

**Healthcheck Issue Resolution:**
Railway tried to healthcheck worker on HTTP endpoint, causing deployment failures. Solution:
1. Created `/railway.toml` at project root without healthcheckPath
2. Worker service uses this config (not backend/railway.toml)
3. API service continues using backend/railway.toml with healthcheck

**Self-Automation via GraphQL API:**
All deployment steps done programmatically:
- Service creation: `serviceCreate` mutation
- GitHub connection: `serviceConnect` mutation
- Environment variables: `variableUpsert` mutation
- Deploy trigger: `serviceInstanceRedeploy` mutation

### Consequences

**Positive:**
- Automated signal generation at 9AM + 12PM EST
- Fully automated deployment (no manual Railway UI needed)
- Independent worker lifecycle from API
- Clear configuration separation

**Negative:**
- Environment variables need to be copied to worker service
- Multiple deployment attempts needed to debug healthcheck issue (6 tries)

**Technical Debt:** None

**Lessons Learned:**
- Celery workers need separate Railway config without healthcheck
- Root-level config file works for services with different rootDirectory settings
- Railway GraphQL API is powerful for infrastructure automation

---

## Decision 14: Backtest Engine Architecture

**Date:** 2026-01-04
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `backtesting`, `portfolio`, `validation`, `post-mvp`

### Context

Need system to validate signal quality before live trading. Key requirements:
- Simulate historical trade execution with realistic assumptions
- Compare different portfolio allocation strategies
- Calculate comprehensive performance metrics (P&L, Sharpe ratio, win rate)
- Track individual agent contribution to performance

### Options Considered

#### Option A: Simple Buy-and-Hold Backtester
**Pros:**
- Easy to implement
- Clear results

**Cons:**
- Doesn't test allocation strategies
- Ignores position sizing
- No stop-loss/take-profit simulation

#### Option B: Full Portfolio Simulator with Allocation Modes (Chosen ✅)
**Pros:**
- Tests different allocation strategies (CORE_FOCUS, BALANCED, DIVERSIFIED)
- Signal ranking by quality score
- Realistic P&L with stop-loss/take-profit
- Agent performance tracking
- Mode comparison endpoint

**Cons:**
- More complex implementation
- Requires market data for exit prices

#### Option C: Event-Driven Backtester
**Pros:**
- Most accurate simulation
- Handles complex scenarios

**Cons:**
- Overkill for MVP validation
- Significantly more complex
- Hard to debug

### Decision

**Chose: Full Portfolio Simulator (Option B)**

**Rationale:**
1. Three allocation modes enable strategy comparison before live trading
2. Signal ranking ensures capital deployed to highest-quality signals first
3. Stop-loss (10%) and take-profit (25%) reflect realistic risk management
4. Agent performance tracking helps tune agent weights
5. Complexity justified by business value - protects capital in production

### Implementation Details

**Three-Stage Pipeline:**
```
Signals → SignalRanker → PortfolioAllocator → BacktestEngine → Results
```

**Signal Ranker Algorithm:**
```python
composite_score = confidence × expected_return × (1 / risk_factor)
```
- Ranks BUY signals by quality score
- Prioritizes high-confidence, high-return, low-risk signals

**Portfolio Allocation Modes:**

| Mode | Core Position | Satellites | Cash Reserve | Risk Level |
|------|---------------|------------|--------------|------------|
| CORE_FOCUS | 60% (1 stock) | 10% each (3 stocks) | 10% | High |
| BALANCED | 40% (1 stock) | 12.5% each (4 stocks) | 10% | Medium |
| DIVERSIFIED | 16% each (5 stocks) | Equal weight | 20% | Low |

**Trade Simulation:**
- Entry: At signal's entry_price
- Exit conditions (whichever first):
  - Hold period expired → exit at market price
  - Stop-loss triggered (-10%) → exit at stop-loss price
  - Take-profit triggered (+25%) → exit at target price

**Performance Metrics:**
- Total P&L (absolute and percentage)
- Win rate (trades with positive P&L)
- Sharpe ratio (risk-adjusted return)
- Max drawdown (largest peak-to-trough decline)
- Per-agent win rate breakdown

### API Endpoints

```
POST /api/v1/backtest/run              - Execute backtest
GET  /api/v1/backtest/{id}/results     - Individual trade results
GET  /api/v1/backtest/{id}/agent-performance - Agent contribution
POST /api/v1/backtest/compare-modes    - Compare all 3 modes
GET  /api/v1/backtest/modes            - Mode descriptions
GET  /api/v1/backtest/history          - Past backtests
```

### Consequences

**Positive:**
- Validates signal quality before risking real capital
- Enables data-driven strategy selection
- Identifies best-performing agents for weight tuning
- Provides confidence metrics for paper trading phase

**Negative:**
- Requires historical market data for accurate exit prices
- Past performance doesn't guarantee future results (standard disclaimer)

**Technical Debt:**
- Currently uses simplified exit price logic (could enhance with real historical OHLC)
- Impact: Low (good enough for validation)

**Business Value:**
- **Risk Reduction:** Test strategies with $0 at risk
- **Strategy Optimization:** Compare CORE_FOCUS vs BALANCED vs DIVERSIFIED
- **Agent Tuning:** Identify which agents contribute most to profitable signals
- **Confidence Building:** Quantitative evidence before live trading

---

## Decision 15: Telegram Bot Architecture

**Date:** 2026-01-05
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `notifications`, `telegram`, `automation`, `post-mvp`

### Context

Need real-time notifications for trading signals. Requirements:
- Real-time alerts when signals with confidence ≥75% are generated
- Daily summary at 8:30 AM EST
- User commands: /signals, /watchlist, /status, /help
- Webhook-based integration (not polling)

### Options Considered

#### Option A: python-telegram-bot with CommandHandlers
**Pros:**
- Built-in command routing
- High-level abstractions
- Well-documented

**Cons:**
- Application/CommandHandler pattern requires running bot loop
- Conflicts with webhook-based FastAPI integration
- Complex async context management

#### Option B: Direct httpx API Calls (Chosen ✅)
**Pros:**
- Simple, direct control
- Works perfectly with FastAPI webhooks
- No complex bot lifecycle management
- Easy to debug and test

**Cons:**
- Manual command parsing needed
- No automatic command registration with BotFather

### Decision

**Chose: Direct httpx API Calls (Option B)**

**Rationale:**
1. Webhooks require stateless request handling - direct API calls fit naturally
2. FastAPI endpoint receives update, processes command, sends response via API
3. No bot "application" loop to manage
4. Simpler error handling and logging
5. Initial implementation with python-telegram-bot handlers failed to respond to webhooks

### Implementation Details

**Architecture:**
```
Telegram → Webhook → FastAPI → TelegramBotService → httpx → Telegram API
                         ↓
                    SQLAlchemy (signals, watchlist)
```

**Files Created:**
- `backend/app/services/telegram_bot.py` - Main bot service
- `backend/app/api/endpoints/telegram.py` - Webhook endpoint
- `backend/app/tasks/telegram_tasks.py` - Celery scheduled tasks

**Bot Commands:**
| Command | Description |
|---------|-------------|
| /start | Welcome message |
| /signals | Latest 5 signals with confidence |
| /watchlist | Current watchlist with tiers |
| /status | System status (agents, signals, DB) |
| /help | Command list |

**Scheduled Tasks (Celery Beat):**
- `telegram-daily-summary` - 8:30 AM EST daily summary
- `telegram-high-confidence-check` - Every 15 min, alert on ≥75% signals

**Environment Variables:**
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Target chat for alerts

### Consequences

**Positive:**
- Real-time notifications without manual checks
- Commands work reliably via webhook
- Simple, maintainable architecture
- Easy to extend with new commands

**Negative:**
- Commands not auto-registered with BotFather (must set manually)
- No inline keyboards or complex UI (not needed for MVP)

**Technical Debt:** None

**Lessons Learned:**
1. python-telegram-bot's Application pattern doesn't fit webhook model
2. Direct API calls via httpx are simpler for webhook integrations
3. Getting chat_id requires temporary webhook deletion + getUpdates polling

---

## Decision 16: Signal Threshold Adjustment

**Date:** 2026-01-06
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `signal-generation`, `algorithm`, `paper-trading`, `post-mvp`

### Context

The Paper Trading Dashboard (14-day validation period starting Jan 5, 2026) was showing 0 signals after 2 days. Investigation revealed:
- Database had 22 signals, but ALL were HOLD
- Paper Trading filters for BUY signals only (actionable for validation)
- Raw scores from agents were typically around 0.1
- Original thresholds required score >= 0.2 for BUY

### Options Considered

#### Option A: Keep Conservative Thresholds
**Pros:**
- Fewer false positives
- More confident signals

**Cons:**
- No actionable signals during validation period
- Can't test the system without signals
- Defeats purpose of paper trading

#### Option B: Adjust Thresholds to Match Score Distribution (Chosen ✅)
**Pros:**
- Generates actionable BUY/SELL signals
- Enables paper trading validation
- Can tune further based on results

**Cons:**
- May generate more signals that don't perform well
- Less conservative approach

#### Option C: Adjust Agent Weights
**Pros:**
- Could amplify scores to hit thresholds

**Cons:**
- More complex change
- Changes consensus dynamics
- Harder to tune

### Decision

**Chose: Adjust Signal Thresholds (Option B)**

**Threshold Changes:**
| Signal Type | Before | After |
|-------------|--------|-------|
| STRONG_BUY | >= 0.6 | >= 0.5 |
| BUY | >= 0.2 | >= 0.1 |
| HOLD | -0.2 to 0.2 | -0.1 to 0.1 |
| SELL | <= -0.2 | <= -0.1 |
| STRONG_SELL | <= -0.6 | <= -0.5 |

**Position Sizing Threshold:**
- Before: score_strength < 0.2 → no position
- After: score_strength < 0.1 → no position

**Rationale:**
1. Raw scores cluster around ±0.1, original thresholds too wide
2. Paper trading needs actionable signals to validate strategy
3. Thresholds can be re-tuned based on 14-day results
4. Better to generate some signals and learn than none
5. Risk: Paper trading, not real money

### Implementation

**File Changed:** `backend/app/agents/signal_generator.py`

```python
def _score_to_signal(self, score: float) -> SignalType:
    """
    Thresholds adjusted for 14-day paper trading validation:
    - More sensitive to generate actionable BUY/SELL signals
    - Neutral zone reduced from ±0.2 to ±0.1
    """
    if score >= 0.5:
        return SignalType.STRONG_BUY
    elif score >= 0.1:
        return SignalType.BUY
    elif score >= -0.1:
        return SignalType.HOLD
    elif score >= -0.5:
        return SignalType.SELL
    else:
        return SignalType.STRONG_SELL
```

**Git Commit:** `518ee0b`

### Results After Fix

| Metric | Before | After |
|--------|--------|-------|
| BUY signals | 0 | 1 (NVDA) |
| SELL signals | 0 | 1 (AAPL) |
| HOLD signals | 22 | 8 |
| Paper Trading Dashboard | 0 signals | 2 BUY signals tracked |

### Consequences

**Positive:**
- Paper Trading validation can now proceed
- System generates diverse signal types
- 12 days remaining to collect performance data
- Can tune thresholds again based on win/loss rate

**Negative:**
- May generate more false positives
- Less conservative than original design

**Mitigation:**
- This is paper trading (no real money at risk)
- 14-day validation period will reveal optimal thresholds
- Can revert or adjust based on results

**Technical Debt:**
- May need threshold re-adjustment after validation period
- Impact: Low (simple configuration change)

**Reversible:** Yes - single line changes in signal_generator.py

**Related Blocker:** #6 (All Signals HOLD)

---

## Decision Template

**Use this template for new decisions:**

```markdown
## Decision X: [Title]

**Date:** YYYY-MM-DD  
**Status:** ⏳ Proposed | ✅ Accepted | ❌ Rejected | 🔄 Superseded  
**Deciders:** [Who made this decision]  
**Tags:** `category`, `milestone-X`

### Context

[What problem are we solving? What constraints exist?]

### Options Considered

#### Option A: [Name]
**Pros:**
- Pro 1
- Pro 2

**Cons:**
- Con 1
- Con 2

**Cost:** $X/mo or free or N/A

#### Option B: [Name]
[Same format]

### Decision

**Chose: [Option X]**

**Rationale:**
1. Reason 1
2. Reason 2
3. Reason 3

### Consequences

**Positive:**
- Good outcome 1
- Good outcome 2

**Negative:**
- Trade-off 1
- Technical debt incurred

**Mitigation:**
- How we'll handle the negatives

**Technical Debt:**
[What will we need to refactor later, or "None"]

**Reversible:**
Yes/No - [Explanation of how hard to change]
```

---

## Decision History

### Superseded Decisions

[Decisions that were later changed/reversed]

**Example:**
```
Decision 5: Use SQLite (superseded by Decision 1)
- Originally chose SQLite for simplicity
- Later switched to PostgreSQL for Celery support
- Date superseded: [Date]
```

---

## Technical Debt Register

**Intentional debt we've incurred:**

1. **Keyword-based sentiment analysis**
   - Why incurred: Faster MVP implementation, no heavy dependencies
   - Impact: Medium (less accurate sentiment scores)
   - Plan to resolve: Upgrade to FinBERT in Milestone 3
   - Related decision: #6

2. **Reddit API integration pending**
   - Why incurred: API credentials not yet available
   - Impact: Medium (missing retail investor sentiment from r/wallstreetbets)
   - Plan to resolve: Add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET to .env when available
   - Related decision: #11
   - **STATUS: WAITING FOR USER TO PROVIDE KEYS**

---

## Future Decisions Needed

**Decisions we know we'll need to make:**

1. **IB vs Alpaca for Live Trading**
   - When: Milestone 6
   - Options: Interactive Brokers (best API) vs Alpaca (easier)
   - Impact: High

2. **Hosting: Railway vs AWS vs Heroku**
   - When: Milestone 6
   - Impact: Medium (cost/complexity)

---

## Lessons Learned

**What we learned from past decisions:**

1. **[Lesson 1]**
   - Decision: #X
   - What we learned: [Insight]
   - Apply to future: [How this informs future choices]

---

**END OF DECISIONS LOG**

*Add to this file whenever you make a non-obvious technical choice. Your future self (or next developer) needs to understand WHY.*
