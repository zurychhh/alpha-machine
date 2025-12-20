# CLAUDE CODE - IMPLEMENTATION GUIDE
## How to Build Alpha Machine with Claude Code Terminal

**Prerequisites:**
- Claude Code installed and authenticated
- Claude Desktop app with Claude Code feature enabled
- Basic terminal knowledge
- Git installed

---

## 🎯 OVERVIEW

You will work with Claude Code in **6 sessions**, one for each milestone.

After each milestone:
1. Claude Code builds and tests
2. You validate the results
3. Return here to discuss progress
4. Proceed to next milestone

---

## 📋 INITIAL SETUP (Do This First)

### 1. Create Project Directory

```bash
mkdir alpha-machine
cd alpha-machine
git init
```

### 2. Copy Documents to Project

Place these 3 files in your project root:
- `BUILD_SPEC.md` (complete technical spec)
- `MILESTONES.md` (6 checkpoints)
- `CLAUDE_CODE_PROMPT.md` (this file)

```bash
# You should have:
alpha-machine/
├── BUILD_SPEC.md
├── MILESTONES.md
└── CLAUDE_CODE_PROMPT.md
```

### 3. Open Claude Code Terminal

In Claude Desktop app:
1. Open terminal (Command Palette → "Claude Code")
2. Navigate to project: `cd /path/to/alpha-machine`

---

## 🤖 SESSION 1: MILESTONE 1 - PROJECT FOUNDATION

### Start Claude Code

In terminal, type:

```
I'm building an AI-powered stock trading system called Alpha Machine.

I have complete technical specifications in BUILD_SPEC.md and milestones in MILESTONES.md.

Let's start with MILESTONE 1: PROJECT FOUNDATION.

Please:
1. Read BUILD_SPEC.md and MILESTONES.md
2. Create the complete project structure as specified
3. Install all dependencies
4. Setup docker-compose with PostgreSQL and Redis
5. Create the database schema
6. Implement the basic FastAPI app with health endpoint
7. Test everything works

Follow the "Definition of Done" tests in MILESTONES.md for Milestone 1.

Start by creating the directory structure. Are you ready?
```

### What Claude Code Will Do

Claude Code will:
- Create all directories (backend/, frontend/, scripts/)
- Generate requirements.txt and package.json
- Create docker-compose.yml
- Create initial database schema SQL
- Implement basic FastAPI app
- Setup .env.example

### Your Job

After Claude Code finishes:

```bash
# 1. Review what was created
ls -la
tree -L 2  # Install tree if needed: brew install tree

# 2. Create your .env file
cp .env.example .env
nano .env  # Add your API keys (leave blank for now)

# 3. Test the setup
docker-compose up -d
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 4. Validate Milestone 1
# Run all tests from MILESTONES.md "Definition of Done" section
docker-compose ps
psql -U alpha -d alphamachine -c "\dt"
```

### Checkpoint

✅ If all tests pass → **Return to main chat, report success, proceed to Session 2**  
❌ If tests fail → **Report specific errors to main chat**

---

## 🤖 SESSION 2: MILESTONE 2 - DATA PIPELINE

### Start Claude Code

```
Milestone 1 complete! ✅

Now let's implement MILESTONE 2: DATA PIPELINE.

Please:
1. Implement app/services/market_data.py (Polygon, Finnhub, Alpha Vantage)
2. Implement app/services/sentiment_data.py (Reddit, NewsAPI)
3. Create SQLAlchemy models for market_data and sentiment_data
4. Implement data aggregator service
5. Add API endpoints for /market-data/{ticker} and /sentiment/{ticker}
6. Test with NVDA ticker

Follow the Milestone 2 Definition of Done tests.

Start with market_data.py. Ready?
```

### What Claude Code Will Do

- Implement all data fetching services
- Create database models
- Add API endpoints
- Create test scripts

### Your Job - Get API Keys

**Before testing, you MUST get API keys:**

1. **Polygon.io:**
   - Go to https://polygon.io/
   - Sign up (FREE tier)
   - Get API key → add to .env: `POLYGON_API_KEY=your_key`

2. **Finnhub:**
   - Go to https://finnhub.io/
   - Sign up (FREE tier)
   - Get API key → add to .env: `FINNHUB_API_KEY=your_key`

3. **Alpha Vantage:**
   - Go to https://www.alphavantage.co/
   - Get free key → add to .env: `ALPHA_VANTAGE_API_KEY=your_key`

4. **Reddit:**
   - Go to https://www.reddit.com/prefs/apps
   - Create app → get client_id and client_secret
   - Add to .env

5. **NewsAPI:**
   - Go to https://newsapi.org/
   - Get free key → add to .env: `NEWS_API_KEY=your_key`

### Test the Pipeline

```bash
# Restart backend to load new .env
docker-compose restart backend

# Test market data
curl http://localhost:8000/api/v1/market-data/NVDA | jq

# Test sentiment
curl http://localhost:8000/api/v1/sentiment/NVDA | jq

# Check database
psql -U alpha -d alphamachine -c "SELECT COUNT(*) FROM market_data;"
```

### Checkpoint

✅ If API keys work and data is fetched → **Return to main chat**  
❌ If 401/403 errors → **Check API keys, report to main chat**

---

## 🤖 SESSION 3: MILESTONE 3 - AI AGENTS

### Start Claude Code

```
Milestone 2 complete! ✅

Now let's build the AI AGENTS for MILESTONE 3.

We need 4 agents:
1. Contrarian Agent (GPT-4) - deep value, contrarian signals
2. Growth Agent (Claude) - momentum, risk-adjusted growth
3. Multi-Modal Agent (Gemini) - charts + news synthesis
4. Predictor Agent (LSTM) - price prediction

Please:
1. Implement base_agent.py abstract class
2. Implement contrarian_agent.py with GPT-4 API
3. Implement growth_agent.py with Anthropic Claude API
4. Implement multimodal_agent.py with Google Gemini API
5. Implement predictor_agent.py (simple LSTM or rule-based for MVP)
6. Create test script to run all agents on NVDA

Each agent must return:
{
  "agent": "name",
  "recommendation": "BUY|SELL|HOLD",
  "confidence": 1-5,
  "reasoning": "why",
  "data_used": {...}
}

Follow BUILD_SPEC.md agent implementations exactly.

Start with base_agent.py. Ready?
```

### Your Job - Get AI API Keys

**Before agents work, get AI keys:**

1. **OpenAI:**
   - Go to https://platform.openai.com/
   - Add $20 credit
   - Get API key → `OPENAI_API_KEY=your_key`

2. **Anthropic:**
   - Go to https://console.anthropic.com/
   - Get API key → `ANTHROPIC_API_KEY=your_key`

3. **Google AI:**
   - Go to https://ai.google.dev/
   - Get API key (FREE) → `GOOGLE_AI_API_KEY=your_key`

### Test Agents

```bash
# Test individual agents
python -c "
from app.agents.contrarian_agent import ContrarianAgent
from app.services.data_aggregator import aggregate_all_data

agent = ContrarianAgent()
data = aggregate_all_data('NVDA')
result = agent.analyze('NVDA', data['market'], data['sentiment'])
print(result)
"

# Test all agents
python scripts/test_agents.py NVDA
```

### Expected Output

```
Agent: contrarian
Recommendation: BUY
Confidence: 4/5
Reasoning: NVDA is oversold with RSI at 28...

Agent: growth
Recommendation: HOLD
Confidence: 3/5
Reasoning: Momentum is neutral, waiting for breakout...

[... etc for all 4 agents]
```

### Checkpoint

✅ If all 4 agents return valid recommendations → **Return to main chat**  
❌ If API errors → **Check keys and budget, report to main chat**

---

## 🤖 SESSION 4: MILESTONE 4 - SIGNAL GENERATION

### Start Claude Code

```
Milestone 3 complete! ✅

Now let's implement SIGNAL GENERATION for MILESTONE 4.

Please:
1. Implement app/services/signal_generator.py
2. Create generate_signal(ticker, db) method that:
   - Fetches market + sentiment data
   - Runs all 4 agents
   - Calculates consensus vote
   - Determines signal type (BUY/SELL/HOLD)
   - Calculates confidence (1-5)
   - Calculates position size, stop loss, target price
   - Stores signal + agent analyses in database
3. Add API endpoint POST /api/v1/signals/generate/{ticker}
4. Add API endpoint GET /api/v1/signals
5. Add API endpoint GET /api/v1/signals/{id}

Consensus rules:
- 4/4 agents agree = confidence 5
- 3/4 agents agree = confidence 4
- 2/4 mixed = confidence 2 (HOLD)

Position sizing:
- Max 10% of capital per position
- Scale by confidence (1-5)

Follow BUILD_SPEC.md signal_generator.py exactly.

Ready?
```

### Test Signal Generation

```bash
# Generate signal for NVDA
curl -X POST http://localhost:8000/api/v1/signals/generate/NVDA | jq

# Expected output:
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

# Check database
psql -U alpha -d alphamachine -c "SELECT * FROM signals;"
psql -U alpha -d alphamachine -c "SELECT agent_name, recommendation FROM agent_analysis WHERE signal_id=1;"
```

### Checkpoint

✅ If signal generated with 4 agent analyses → **Return to main chat**  
❌ If consensus logic wrong → **Report issue to main chat**

---

## 🤖 SESSION 5: MILESTONE 5 - DASHBOARD

### Start Claude Code

```
Milestone 4 complete! ✅

Now let's build the REACT DASHBOARD for MILESTONE 5.

Please:
1. Initialize frontend with Vite + React + TypeScript
2. Install Tailwind CSS
3. Implement src/services/api.ts (API client)
4. Create Dashboard page showing all signals
5. Create SignalCard component
6. Create SignalDetailsModal showing agent reasoning
7. Make it responsive (mobile + desktop)

The dashboard should:
- Load signals from backend API
- Separate strong signals (confidence ≥4) from weak
- Display ticker, price, signal type, confidence (stars)
- Click signal → modal with all 4 agent votes + reasoning
- Auto-refresh every 5 minutes

Follow BUILD_SPEC.md frontend implementation.

Ready?
```

### Test Dashboard

```bash
cd frontend
npm run dev

# Open http://localhost:5173
# You should see:
# - List of signals
# - Click any signal → modal with agent reasoning
```

### Checkpoint

✅ If dashboard loads and shows signals → **Return to main chat**  
❌ If CORS errors → **Report to main chat (need to configure backend)**

---

## 🤖 SESSION 6: MILESTONE 6 - AUTOMATION & DEPLOYMENT

### Start Claude Code

```
Milestone 5 complete! ✅

Final milestone: AUTOMATION & DEPLOYMENT.

Please:
1. Setup Celery with Redis
2. Create scheduled tasks:
   - fetch_market_data_task (every 5 min)
   - fetch_sentiment_task (every 30 min)
   - generate_signals_task (daily at 9am EST)
3. Implement paper trading simulation
4. Add task monitoring/logging
5. Prepare for deployment:
   - Railway backend setup guide
   - Vercel frontend setup guide

Follow MILESTONES.md Milestone 6 tasks.

Ready?
```

### Deploy to Production

**Backend (Railway):**
1. Go to https://railway.app/
2. Connect GitHub repo
3. Add PostgreSQL + Redis services
4. Set environment variables (all API keys)
5. Deploy backend
6. Test: `curl https://your-app.railway.app/health`

**Frontend (Vercel):**
1. Go to https://vercel.com/
2. Connect GitHub repo
3. Set env var: `VITE_API_URL=https://your-app.railway.app/api/v1`
4. Deploy frontend
5. Test: Open Vercel URL, dashboard should load

### Final Validation

```bash
# Let system run for 24 hours
# Check logs for any crashes
# Verify scheduled tasks running
# Check signals being generated automatically
```

### Checkpoint

✅ If deployed and running 24h without crashes → **🎉 SYSTEM COMPLETE!**  
❌ If deployment issues → **Report to main chat**

---

## 🎓 TIPS FOR WORKING WITH CLAUDE CODE

### 1. Be Specific

❌ Bad: "Build the backend"  
✅ Good: "Implement app/services/market_data.py with Polygon.io integration as specified in BUILD_SPEC.md lines 200-250"

### 2. Reference Documentation

Always say: "Follow BUILD_SPEC.md section X" or "Follow MILESTONES.md Milestone Y"

### 3. Test Incrementally

After each component:
- Ask Claude Code to create a test
- Run the test
- Fix issues before proceeding

### 4. Handle Errors

If something fails:
1. Copy exact error message
2. Ask Claude Code: "I got this error: [paste]. How do I fix it?"
3. If stuck, return to main chat

### 5. Save Progress

After each working milestone:
```bash
git add .
git commit -m "Milestone X complete"
git tag milestone-X
```

### 6. Rollback if Needed

```bash
# If milestone fails badly
git reset --hard milestone-3  # Go back to last working state
# Then retry from that point
```

---

## 📞 WHEN TO RETURN TO MAIN CHAT

**Return to main chat after each milestone to:**
- ✅ Report success → Get approval to proceed
- ❌ Report blockers → Get help debugging
- 💡 Ask architecture questions → Before implementing
- 🔑 Confirm API keys working → Before proceeding
- 📊 Discuss results → After testing

**Don't stay stuck in Claude Code!** If you're blocked for >15 min, come back to main chat.

---

## ✅ SUCCESS CHECKLIST

By end of all 6 sessions, you should have:

- [ ] Complete project structure
- [ ] Working data pipeline (market + sentiment)
- [ ] 4 AI agents analyzing stocks
- [ ] Multi-agent consensus signals
- [ ] React dashboard showing signals
- [ ] Scheduled automated tasks
- [ ] Paper trading mode
- [ ] Deployed to Railway + Vercel
- [ ] Running 24/7 without crashes

---

## 🚀 READY TO START?

1. Copy BUILD_SPEC.md, MILESTONES.md, and this file to your project
2. Open Claude Code terminal
3. Navigate to project directory
4. Start with SESSION 1 prompt above
5. Return here after each milestone

**Good luck! Let's build your Alpha Machine.** ⚡

---

**END OF CLAUDE CODE GUIDE**
