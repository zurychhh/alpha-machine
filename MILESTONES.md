# ALPHA MACHINE - IMPLEMENTATION MILESTONES
## 6 Checkpoints with Definition of Done

**Timeline:** 2 weeks  
**Review Frequency:** After each milestone completion  
**Rollback Strategy:** Git tag each milestone

---

## 🎯 MILESTONE 1: PROJECT FOUNDATION
**Duration:** Days 1-2  
**Goal:** Complete project setup, dependencies, database

### Tasks

#### 1.1 Project Structure
- [ ] Create complete directory structure (backend/ frontend/ scripts/)
- [ ] Initialize Git repository
- [ ] Create .gitignore (exclude .env, __pycache__, node_modules)
- [ ] Setup virtual environment (Python 3.11+)

#### 1.2 Dependencies
- [ ] Create requirements.txt with all backend deps
- [ ] Create package.json with all frontend deps
- [ ] Install backend: `pip install -r requirements.txt`
- [ ] Install frontend: `npm install`

#### 1.3 Environment Configuration
- [ ] Create .env.example template
- [ ] Create .env with placeholder API keys
- [ ] Configure settings in app/core/config.py
- [ ] Test settings load: `python -c "from app.core.config import settings; print(settings.PROJECT_NAME)"`

#### 1.4 Database Setup
- [ ] Create docker-compose.yml (PostgreSQL + Redis)
- [ ] Start containers: `docker-compose up -d`
- [ ] Run schema SQL: `psql < scripts/setup_db.sql`
- [ ] Verify tables created: `psql -c "\dt"`

#### 1.5 Basic API
- [ ] Create app/main.py with FastAPI app
- [ ] Add health endpoint: GET /health
- [ ] Start server: `uvicorn app.main:app --reload`
- [ ] Test: `curl http://localhost:8000/health`

### Definition of Done

**Tests to Pass:**
```bash
# 1. Docker containers running
docker-compose ps | grep "Up"

# 2. Database accessible
psql -c "SELECT COUNT(*) FROM watchlist;"

# 3. API responding
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 4. No syntax errors
python -m py_compile app/**/*.py
```

**Success Criteria:**
- ✅ All Docker services running
- ✅ PostgreSQL has 7 tables (watchlist, signals, agent_analysis, portfolio, performance, market_data, sentiment_data)
- ✅ Redis accessible on localhost:6379
- ✅ FastAPI health endpoint returns 200
- ✅ No Python syntax errors

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 1: Project foundation complete"
git tag milestone-1
```

---

## 🎯 MILESTONE 2: DATA PIPELINE
**Duration:** Days 3-4  
**Goal:** Fetch market data + sentiment, store in database

### Tasks

#### 2.1 Market Data Service
- [ ] Implement app/services/market_data.py
- [ ] Add get_current_price() method
- [ ] Add get_historical_data() method
- [ ] Add get_technical_indicators() method
- [ ] Test with NVDA ticker

#### 2.2 Sentiment Data Service
- [ ] Implement app/services/sentiment_data.py
- [ ] Setup Reddit API (PRAW)
- [ ] Add get_reddit_sentiment() method
- [ ] Add get_news_sentiment() method
- [ ] Add aggregate_sentiment() method

#### 2.3 Data Models
- [ ] Create SQLAlchemy models (market_data, sentiment_data)
- [ ] Create Pydantic schemas for validation
- [ ] Add CRUD operations

#### 2.4 Data Aggregator
- [ ] Implement app/services/data_aggregator.py
- [ ] Create aggregate_all_data(ticker) method
- [ ] Store fetched data in PostgreSQL
- [ ] Add error handling + logging

#### 2.5 API Endpoints
- [ ] GET /api/v1/market-data/{ticker}
- [ ] GET /api/v1/sentiment/{ticker}
- [ ] Test endpoints with Postman/curl

### Definition of Done

**Tests to Pass:**
```bash
# 1. Test market data fetch
python scripts/test_apis.py
# Expected: ✅ Polygon.io, ✅ Finnhub, ✅ Alpha Vantage

# 2. Test sentiment fetch
curl http://localhost:8000/api/v1/sentiment/NVDA
# Expected: JSON with reddit + news sentiment

# 3. Verify data in database
psql -c "SELECT COUNT(*) FROM market_data;"
psql -c "SELECT COUNT(*) FROM sentiment_data;"
# Expected: >0 rows

# 4. Test data aggregator
python -c "
from app.services.data_aggregator import aggregate_all_data
data = aggregate_all_data('NVDA')
print('Current price:', data['market']['current_price'])
print('Sentiment score:', data['sentiment']['combined_sentiment'])
"
```

**Success Criteria:**
- ✅ Can fetch current price for any stock (Polygon)
- ✅ Can fetch historical 30-day data (Alpha Vantage)
- ✅ Can fetch Reddit sentiment (PRAW)
- ✅ Can fetch news sentiment (NewsAPI)
- ✅ All data stored in PostgreSQL
- ✅ API endpoints return valid JSON
- ✅ Error handling works (try with invalid ticker)

**Sample Output:**
```json
{
  "ticker": "NVDA",
  "market": {
    "current_price": 875.50,
    "rsi": 62.3,
    "volume_trend": "increasing"
  },
  "sentiment": {
    "combined_sentiment": 0.72,
    "reddit_mentions": 1247,
    "news_articles": 15
  }
}
```

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 2: Data pipeline complete"
git tag milestone-2
```

---

## 🎯 MILESTONE 3: AI AGENTS
**Duration:** Days 5-7  
**Goal:** Implement 4 AI agents, test individual recommendations

### Tasks

#### 3.1 Base Agent Class
- [ ] Create app/agents/base_agent.py
- [ ] Define abstract analyze() method
- [ ] Add _build_recommendation() helper

#### 3.2 Contrarian Agent (GPT-4)
- [ ] Implement app/agents/contrarian_agent.py
- [ ] Create contrarian analysis prompt
- [ ] Parse JSON response
- [ ] Test with NVDA (should detect oversold/overbought)

#### 3.3 Growth Agent (Claude)
- [ ] Implement app/agents/growth_agent.py
- [ ] Create momentum analysis prompt
- [ ] Parse JSON response
- [ ] Test with PLTR (high growth stock)

#### 3.4 Multi-Modal Agent (Gemini)
- [ ] Implement app/agents/multimodal_agent.py
- [ ] Combine price charts + news analysis
- [ ] Parse JSON response
- [ ] Test with AMD

#### 3.5 Predictor Agent (LSTM)
- [ ] Implement app/ml/lstm_model.py
- [ ] Train on 6 months historical data
- [ ] Save model weights
- [ ] Implement app/agents/predictor_agent.py
- [ ] Return BUY if predicted price > current +5%

### Definition of Done

**Tests to Pass:**
```bash
# 1. Test each agent individually
python -c "
from app.agents.contrarian_agent import ContrarianAgent
from app.services.data_aggregator import aggregate_all_data

agent = ContrarianAgent()
data = aggregate_all_data('NVDA')
result = agent.analyze('NVDA', data['market'], data['sentiment'])

print(f\"Agent: {result['agent']}\")
print(f\"Recommendation: {result['recommendation']}\")
print(f\"Confidence: {result['confidence']}/5\")
print(f\"Reasoning: {result['reasoning']}\")
"
# Expected: Valid BUY/SELL/HOLD with reasoning

# 2. Test all 4 agents on same stock
python scripts/test_agents.py NVDA
# Expected: 4 recommendations printed

# 3. Verify different perspectives
python scripts/test_agents.py PLTR
# Growth agent should be more bullish than contrarian
```

**Success Criteria:**
- ✅ GPT-4 agent returns valid JSON
- ✅ Claude agent returns valid JSON
- ✅ Gemini agent returns valid JSON
- ✅ LSTM agent predicts price direction
- ✅ Each agent has distinct "personality" (contrarian ≠ growth)
- ✅ Confidence scores range 1-5
- ✅ Reasoning is clear and actionable
- ✅ All agents handle API failures gracefully (return HOLD)

**Sample Agent Output:**
```json
{
  "agent": "contrarian",
  "recommendation": "BUY",
  "confidence": 4,
  "reasoning": "NVDA is oversold (RSI: 28) with negative sentiment (-0.4). Contrarian opportunity as market is overly fearful.",
  "data_used": {
    "current_price": 850.00,
    "rsi": 28,
    "sentiment": -0.4
  }
}
```

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 3: AI agents complete"
git tag milestone-3
```

---

## 🎯 MILESTONE 4: SIGNAL GENERATION
**Duration:** Days 8-9  
**Goal:** Multi-agent consensus, signal creation, position sizing

### Tasks

#### 4.1 Signal Generator Service
- [ ] Implement app/services/signal_generator.py
- [ ] Create generate_signal(ticker) method
- [ ] Orchestrate all 4 agents
- [ ] Calculate consensus (voting algorithm)

#### 4.2 Consensus Algorithm
- [ ] Count BUY/SELL/HOLD votes
- [ ] Calculate confidence (4/4=5, 3/4=4, etc.)
- [ ] Determine final signal type
- [ ] Log reasoning from all agents

#### 4.3 Position Sizing
- [ ] Implement _calculate_position_size() method
- [ ] Scale by confidence (1-5)
- [ ] Respect max position size (10% capital)
- [ ] Calculate number of shares

#### 4.4 Risk Parameters
- [ ] Calculate stop loss (10% below entry)
- [ ] Calculate take profit targets (25%, 50%, 100%)
- [ ] Store in signals table

#### 4.5 API Endpoints
- [ ] POST /api/v1/signals/generate/{ticker}
- [ ] GET /api/v1/signals (list all signals)
- [ ] GET /api/v1/signals/{id} (signal details + agent analyses)

### Definition of Done

**Tests to Pass:**
```bash
# 1. Generate signal for NVDA
curl -X POST http://localhost:8000/api/v1/signals/generate/NVDA

# Expected response:
{
  "id": 1,
  "ticker": "NVDA",
  "signal_type": "BUY",
  "confidence": 4,
  "entry_price": 875.50,
  "stop_loss": 788.00,
  "target_price": 1094.38,
  "position_size": 45,
  "status": "PENDING"
}

# 2. Verify signal in database
psql -c "SELECT * FROM signals WHERE ticker='NVDA';"

# 3. Check agent analyses saved
psql -c "SELECT agent_name, recommendation FROM agent_analysis WHERE signal_id=1;"

# Expected: 4 rows (contrarian, growth, multimodal, predictor)

# 4. Test consensus scenarios
python scripts/test_consensus.py
# Scenarios:
# - All agree BUY → confidence=5
# - 3/4 BUY → confidence=4
# - 2 BUY, 2 HOLD → confidence=2 (weak signal)
```

**Success Criteria:**
- ✅ Signal generated with all required fields
- ✅ Consensus algorithm works correctly
- ✅ Position size calculated (respects 10% max)
- ✅ Stop loss = entry * 0.90
- ✅ Target = entry * 1.25
- ✅ All 4 agent analyses saved to database
- ✅ Confidence matches vote count
- ✅ API returns signal JSON

**Validation Rules:**
| Votes | Signal | Confidence |
|-------|--------|------------|
| 4/4 BUY | BUY | 5 |
| 3/4 BUY | BUY | 4 |
| 2/4 BUY, 2 HOLD | HOLD | 2 |
| 2/4 BUY, 2 SELL | HOLD | 0 |
| 4/4 SELL | SELL | 5 |

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 4: Signal generation complete"
git tag milestone-4
```

---

## 🎯 MILESTONE 5: DASHBOARD
**Duration:** Days 10-12  
**Goal:** React frontend to display signals, agent reasoning, portfolio

### Tasks

#### 5.1 Frontend Setup
- [ ] Initialize Vite + React + TypeScript
- [ ] Setup Tailwind CSS
- [ ] Create routing (react-router-dom)
- [ ] Create layout components

#### 5.2 API Client
- [ ] Implement src/services/api.ts
- [ ] Add getSignals() method
- [ ] Add getSignalDetails() method
- [ ] Add getPortfolio() method

#### 5.3 Dashboard Page
- [ ] Create src/pages/Dashboard.tsx
- [ ] Display today's signals
- [ ] Separate strong (4-5) vs weak (1-3) signals
- [ ] Auto-refresh every 5 minutes

#### 5.4 Signal Card Component
- [ ] Create src/components/SignalCard.tsx
- [ ] Show ticker, price, signal type
- [ ] Show confidence (1-5 stars)
- [ ] Click to view agent reasoning

#### 5.5 Signal Details Modal
- [ ] Create src/components/SignalDetailsModal.tsx
- [ ] Display all 4 agent votes
- [ ] Show individual reasoning
- [ ] Show entry/exit prices, position size
- [ ] Add "Approve" button (manual override)

#### 5.6 Portfolio View
- [ ] Create src/pages/Portfolio.tsx
- [ ] Show current positions
- [ ] Show unrealized P&L
- [ ] Show performance chart

### Definition of Done

**Tests to Pass:**
```bash
# 1. Frontend builds without errors
cd frontend
npm run build
# Expected: dist/ folder created

# 2. Frontend runs locally
npm run dev
# Expected: Server on http://localhost:5173

# 3. API calls work
# Open http://localhost:5173
# Click on a signal
# Expected: Modal shows agent reasoning

# 4. Responsive design
# Resize browser to mobile size
# Expected: Layout adapts (cards stack vertically)
```

**Success Criteria:**
- ✅ Dashboard loads and displays signals
- ✅ Signal cards show ticker, price, confidence
- ✅ Click signal → modal shows 4 agent analyses
- ✅ Agent reasoning is readable and formatted
- ✅ Portfolio page shows positions + P&L
- ✅ Auto-refresh works (every 5 min)
- ✅ Responsive design (mobile + desktop)
- ✅ No console errors

**UI Mockup:**
```
┌─────────────────────────────────────────┐
│ Alpha Machine Dashboard                 │
├─────────────────────────────────────────┤
│ 🔥 Strong Signals (3)                   │
│                                         │
│ ┌─────┐ ┌─────┐ ┌─────┐                │
│ │NVDA │ │PLTR │ │AMD  │                │
│ │ BUY │ │ BUY │ │ BUY │                │
│ │⭐⭐⭐⭐⭐│ │⭐⭐⭐⭐  │ │⭐⭐⭐⭐  │                │
│ │$875 │ │$42  │ │$180 │                │
│ └─────┘ └─────┘ └─────┘                │
│                                         │
│ 📊 Weak Signals (2)                     │
│ ┌─────┐ ┌─────┐                        │
│ │GOOGL│ │MSFT │                        │
│ │HOLD │ │HOLD │                        │
│ │⭐⭐    │ │⭐⭐⭐  │                        │
│ └─────┘ └─────┘                        │
└─────────────────────────────────────────┘
```

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 5: Dashboard complete"
git tag milestone-5
```

---

## 🎯 MILESTONE 6: AUTOMATION & DEPLOYMENT
**Duration:** Days 13-14  
**Goal:** Scheduled tasks, paper trading, deployment

### Tasks

#### 6.1 Celery Setup
- [ ] Create app/tasks/celery_app.py
- [ ] Configure Celery with Redis broker
- [ ] Add celery worker to docker-compose

#### 6.2 Scheduled Tasks
- [ ] Create app/tasks/data_tasks.py
- [ ] Add fetch_market_data_task() - runs every 5 min
- [ ] Add fetch_sentiment_task() - runs every 30 min
- [ ] Create app/tasks/signal_tasks.py
- [ ] Add generate_signals_task() - runs daily at 9am EST

#### 6.3 Paper Trading Mode
- [ ] Implement app/services/paper_trading.py
- [ ] Simulate order execution
- [ ] Track simulated P&L
- [ ] Store in performance table

#### 6.4 Notifications
- [ ] Setup Telegram bot (optional)
- [ ] Send alert when signal confidence ≥4
- [ ] Include ticker, signal type, reasoning

#### 6.5 Deployment
- [ ] Deploy backend to Railway
- [ ] Setup PostgreSQL + Redis on Railway
- [ ] Deploy frontend to Vercel
- [ ] Configure CORS
- [ ] Setup environment variables

#### 6.6 Monitoring
- [ ] Add logging (Python logging)
- [ ] Log all signals generated
- [ ] Log all trades executed
- [ ] Setup error alerts

### Definition of Done

**Tests to Pass:**
```bash
# 1. Celery worker running
celery -A app.tasks.celery_app worker --loglevel=info
# Expected: Worker starts, no errors

# 2. Test scheduled task manually
python -c "
from app.tasks.data_tasks import fetch_market_data_task
result = fetch_market_data_task.delay()
print('Task ID:', result.id)
"
# Expected: Task ID printed, data fetched

# 3. Test paper trading
curl -X POST http://localhost:8000/api/v1/paper-trade/execute/1
# Expected: Simulated trade executed, P&L calculated

# 4. Test deployment
curl https://your-backend.railway.app/health
# Expected: {"status": "healthy"}

curl https://your-frontend.vercel.app
# Expected: Dashboard loads
```

**Success Criteria:**
- ✅ Celery tasks run on schedule
- ✅ Data fetched automatically every 5 min
- ✅ Signals generated daily at 9am EST
- ✅ Paper trading simulates trades correctly
- ✅ P&L tracking works
- ✅ Backend deployed to Railway (accessible via URL)
- ✅ Frontend deployed to Vercel (accessible via URL)
- ✅ Logs show all activity
- ✅ No crashes or errors for 24 hours

**Celery Schedule:**
```python
# app/tasks/celery_app.py
from celery.schedules import crontab

beat_schedule = {
    'fetch-market-data': {
        'task': 'app.tasks.data_tasks.fetch_market_data_task',
        'schedule': 300.0,  # Every 5 minutes
    },
    'fetch-sentiment': {
        'task': 'app.tasks.data_tasks.fetch_sentiment_task',
        'schedule': 1800.0,  # Every 30 minutes
    },
    'generate-signals': {
        'task': 'app.tasks.signal_tasks.generate_signals_task',
        'schedule': crontab(hour=9, minute=0),  # 9am EST daily
    },
}
```

**Deployment Checklist:**
- [ ] Railway account created
- [ ] PostgreSQL provisioned on Railway
- [ ] Redis provisioned on Railway
- [ ] Environment variables set on Railway
- [ ] Backend deployed, health check passes
- [ ] Vercel account created
- [ ] Frontend connected to Railway backend URL
- [ ] Frontend deployed, loads correctly
- [ ] CORS configured (allow Vercel domain)

**Git Checkpoint:**
```bash
git add .
git commit -m "Milestone 6: Automation & deployment complete"
git tag milestone-6
git push origin main --tags
```

---

## ✅ FINAL VALIDATION

**System Integration Test:**
```bash
# 1. Start all services
docker-compose up -d
celery -A app.tasks.celery_app worker &
celery -A app.tasks.celery_app beat &
uvicorn app.main:app --reload &

# 2. Wait 10 minutes for automated tasks

# 3. Check signals generated
curl http://localhost:8000/api/v1/signals | jq

# Expected: At least 5 signals for different tickers

# 4. Open dashboard
open http://localhost:5173

# Expected: All signals displayed with agent reasoning
```

**Performance Metrics:**
- [ ] Data fetch latency <5 seconds
- [ ] Signal generation <30 seconds (all 4 agents)
- [ ] Dashboard load time <2 seconds
- [ ] API response time <500ms
- [ ] Zero crashes in 24-hour test

**Ready for Live Trading When:**
- ✅ All 6 milestones complete
- ✅ Paper trading shows positive results (win rate >60%)
- ✅ System runs 24 hours without errors
- ✅ All tests pass
- ✅ IB account approved and funded
- ✅ User comfortable with signal quality

---

## 🔄 ROLLBACK PROCEDURE

If any milestone fails:

```bash
# 1. Check which milestone failed
git log --oneline

# 2. Rollback to last working milestone
git reset --hard milestone-3  # Example: rollback to milestone 3

# 3. Fix issues

# 4. Retry from that milestone
```

---

**END OF MILESTONES**

*Return to this document after each milestone to validate completion before proceeding.*
