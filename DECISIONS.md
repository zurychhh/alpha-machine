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
5. [Flexible package versions for Python 3.13](#decision-5-flexible-versions)
6. [Defer TensorFlow to Milestone 3](#decision-6-defer-tensorflow)
7. [Example Decision Template](#decision-template)

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

BUILD_SPEC.md specified `psycopg2-binary==2.9.9` but this package failed to build on Python 3.13 due to C extension compatibility issues.

### Options Considered

#### Option A: psycopg2-binary (Original spec)
**Pros:**
- As specified in BUILD_SPEC.md
- Widely used, well-documented

**Cons:**
- Fails to compile on Python 3.13
- Uses older C API
- No Python 3.13 wheel available

#### Option B: psycopg[binary]>=3.1.18 (Chosen ✅)
**Pros:**
- Native Python 3.13 support
- Modern async support built-in
- Pure Python with optional C extension
- Active development

**Cons:**
- Slightly different API (SQLAlchemy dialect: `postgresql+psycopg://`)
- Minor code change needed in database.py

### Decision

**Chose: psycopg3 (Option B)**

**Rationale:**
1. Python 3.13 compatibility is required (current environment)
2. psycopg3 is the future - psycopg2 is maintenance-only
3. SQLAlchemy supports psycopg3 natively
4. Simple fix: change dialect in connection string

### Consequences

**Positive:**
- Works with Python 3.13
- Future-proof choice
- Better async support for later

**Negative:**
- Deviates from BUILD_SPEC.md
- Required adding URL conversion in database.py

**Code Changes:**
- `requirements.txt`: `psycopg[binary]>=3.1.18`
- `database.py`: Added dialect conversion `postgresql://` → `postgresql+psycopg://`

**Technical Debt:** None
**Reversible:** Yes, if switching to older Python

---

## Decision 5: Flexible Package Versions for Python 3.13

**Date:** 2025-12-20
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `dependencies`, `python`, `milestone-1`

### Context

BUILD_SPEC.md specified exact versions (e.g., `pandas==2.1.4`, `numpy==1.26.3`) which are incompatible with Python 3.13.

### Options Considered

#### Option A: Exact versions (Original spec)
**Pros:**
- Reproducible builds
- As specified

**Cons:**
- Won't install on Python 3.13
- Old packages with potential security issues

#### Option B: Minimum versions with >= (Chosen ✅)
**Pros:**
- Python 3.13 compatible
- Gets latest security patches
- Still maintains minimum functionality

**Cons:**
- Less reproducible (versions may drift)
- Potential compatibility issues with newer versions

### Decision

**Chose: Flexible versions (Option B)**

**Rationale:**
1. Python 3.13 is current environment - must work
2. Semantic versioning means minor updates are compatible
3. Can pin versions later if issues arise
4. Production deployment will lock versions anyway

### Consequences

**Positive:**
- All packages install successfully
- Latest security patches included
- pandas 2.3.3, numpy 2.3.5 work great

**Negative:**
- Versions may differ from BUILD_SPEC.md examples
- Need to test if newer versions break anything

**Technical Debt:** Consider creating `requirements.lock` for production
**Reversible:** Yes, can pin versions anytime

---

## Decision 6: Defer TensorFlow to Milestone 3

**Date:** 2025-12-20
**Status:** ✅ Accepted
**Deciders:** Claude Code
**Tags:** `ml`, `dependencies`, `milestone-1`

### Context

BUILD_SPEC.md includes TensorFlow and transformers in requirements.txt, but these are only needed for Milestone 3 (LSTM agent). They are heavy packages (~2GB) and have complex Python 3.13 compatibility.

### Options Considered

#### Option A: Install all packages upfront
**Pros:**
- Matches BUILD_SPEC.md exactly
- All deps ready when needed

**Cons:**
- TensorFlow 2.15.0 may not support Python 3.13
- Adds 2GB+ to environment
- Slows down pip install significantly
- Not needed until Milestone 3

#### Option B: Defer heavy ML packages (Chosen ✅)
**Pros:**
- Faster initial setup
- Avoid compatibility issues now
- Only install when actually needed
- Smaller venv for M1-M2

**Cons:**
- Deviates from BUILD_SPEC.md
- Will need to add later

### Decision

**Chose: Defer TensorFlow/transformers (Option B)**

**Rationale:**
1. Not needed until Milestone 3 (AI Agents - LSTM)
2. Avoid Python 3.13 compatibility debugging now
3. Faster development iteration for M1-M2
4. Can add with tested versions when needed

### Consequences

**Positive:**
- Faster pip install (~30s vs ~5min)
- No TensorFlow compatibility issues
- Lighter virtual environment

**Negative:**
- Need to add packages in Milestone 3
- May discover issues later

**Technical Debt:** Add TensorFlow, transformers in M3 requirements
**Reversible:** Yes, just add to requirements.txt later

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

1. **[Debt Item 1]**
   - Why incurred: [Reason]
   - Impact: Low/Medium/High
   - Plan to resolve: [When/how]
   - Related decision: #X

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
