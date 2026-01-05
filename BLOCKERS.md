# ALPHA MACHINE - BLOCKERS & ISSUES LOG
## Problems, Solutions, Workarounds

**Purpose:** Track all problems encountered and how they were resolved  
**Updated By:** Claude Code (whenever a blocker occurs)  
**Status:** Update when blocker is resolved

---

## 🚨 ACTIVE BLOCKERS

**Current Count:** 0

None - all clear ✅

**Last Updated:** 2026-01-04

---

## 🟢 RESOLVED BLOCKERS (Session 11 - Backtest Engine)

### Blocker #3: SQLAlchemy Mock Chain TypeError

**Date Opened:** 2026-01-04
**Date Resolved:** 2026-01-04
**Severity:** 🟡 Medium
**Status:** 🟢 Resolved

**Description:**
Unit tests for BacktestEngine failed with `TypeError: object of type 'Mock' has no len()` when testing SQLAlchemy query chains.

**Error Message:**
```
TypeError: object of type 'Mock' has no len()
```

**Impact:**
- Blocked test execution for backtesting module
- Could not validate BacktestEngine logic

**Root Cause:**
Standard `Mock()` doesn't implement magic methods like `__len__`. SQLAlchemy's `.all()` returns a list, which needs length support.

**Solution:**
```python
# Przed (błąd)
mock_db = Mock()

# Po (fix)
mock_db = MagicMock()  # MagicMock implements __len__, __iter__, etc.
```

**Code Changes:**
- `tests/unit/test_backtesting.py`: Changed all `Mock()` to `MagicMock()` for db mocks

**Time Lost:** ~10 minutes
**Lesson Learned:** Always use `MagicMock` when mocking objects that need magic method support

---

### Blocker #4: PostgreSQL Timestamp vs String Comparison

**Date Opened:** 2026-01-04
**Date Resolved:** 2026-01-04
**Severity:** 🔴 High
**Status:** 🟢 Resolved

**Description:**
Backtest API endpoint returned `500 Internal Server Error` on production. SQLAlchemy query failed when comparing timestamp column with string dates.

**Error Message:**
```
ProgrammingError: operator does not exist: timestamp without time zone >= character varying
HINT: No operator matches the given name and argument types.
```

**Impact:**
- Blocked entire Backtest Engine on production
- API returned 500 instead of results

**Root Cause:**
PostgreSQL cannot compare `timestamp` column directly with `varchar` string. SQLAlchemy was passing date strings like `"2026-01-01"` directly to the query filter.

**Solution:**
```python
# Przed (błąd)
Signal.timestamp >= start_date  # start_date = "2026-01-01" (string)

# Po (fix)
start_dt = datetime.strptime(start_date, "%Y-%m-%d")
end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
Signal.timestamp >= start_dt  # datetime object
Signal.timestamp <= end_dt
```

**Code Changes:**
- `backend/app/services/backtesting.py`: Added date string to datetime conversion

**Time Lost:** ~15 minutes
**Lesson Learned:** Always convert string dates to datetime objects before SQLAlchemy timestamp comparisons

---

## 🟢 RESOLVED BLOCKERS (Milestone 1)

### Blocker #1: psycopg2-binary Build Failure on Python 3.13

**Date Opened:** 2025-12-20
**Date Resolved:** 2025-12-20
**Severity:** 🔴 High
**Status:** 🟢 Resolved

**Description:**
`pip install psycopg2-binary==2.9.9` failed during Milestone 1 setup. The package couldn't build C extensions on Python 3.13 due to API changes in the Python C API.

**Error Message:**
```
pg_config executable not found.
error: metadata-generation-failed
```

**Impact:**
- Blocked all database connectivity
- Couldn't proceed with Milestone 1

**Solution:**
1. Replaced `psycopg2-binary==2.9.9` with `psycopg[binary]>=3.1.18`
2. Updated SQLAlchemy connection string dialect in `database.py`
3. Added URL conversion: `postgresql://` → `postgresql+psycopg://`

**Code Changes:**
- `requirements.txt`: Changed psycopg2 to psycopg3
- `database.py`: Added dialect conversion

**Workaround Used:** N/A (proper fix implemented)

**Prevention:**
- Document Python 3.13 compatibility in STATUS.md
- Test requirements on target Python version early

**Time Lost:** ~15 minutes
**Lesson Learned:** Always check package Python version compatibility before assuming BUILD_SPEC.md versions will work

---

### Blocker #2: pandas 2.1.4 Build Failure on Python 3.13

**Date Opened:** 2025-12-20
**Date Resolved:** 2025-12-20
**Severity:** 🔴 High
**Status:** 🟢 Resolved

**Description:**
`pandas==2.1.4` failed to build on Python 3.13 due to numpy C API changes.

**Error Message:**
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> pandas
```

**Impact:**
- Blocked dependency installation
- Couldn't proceed with pip install

**Solution:**
1. Changed all exact versions (`==`) to minimum versions (`>=`)
2. Updated to `pandas>=2.2.0` and `numpy>=2.0.0`
3. Let pip resolve compatible versions for Python 3.13

**Final Versions Installed:**
- pandas 2.3.3
- numpy 2.3.5

**Time Lost:** ~5 minutes
**Lesson Learned:** Use flexible versioning for evolving Python versions

---

### [Template] Blocker #X: [Title]

**Date Opened:** YYYY-MM-DD  
**Severity:** 🔴 High | 🟡 Medium | 🟢 Low  
**Impact:** [What's blocked? Which milestone?]  
**Status:** 🔴 Open | 🟡 In Progress | 🟢 Resolved  

**Description:**
[Clear description of the problem]

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. Error occurs

**Error Message:**
```
[Paste exact error if applicable]
```

**Attempted Solutions:**
1. **Tried X** - Didn't work because Y
2. **Tried Z** - Partial success but...
3. **Research:** [Links to Stack Overflow, docs, etc.]

**Current Workaround:**
[Temporary solution being used, or "None"]

**Needs:**
- [ ] User input/decision
- [ ] API key / credentials
- [ ] Third-party service fix
- [ ] Code refactor
- [ ] External dependency

**Related:**
- Milestone: [X]
- File: `path/to/file.py`
- Function: `function_name()`
- Decision: [DECISIONS.md #X if applicable]

**Notes:**
[Any additional context]

---

## 🟢 RESOLVED BLOCKERS

### Blocker #2: Alpha Vantage Rate Limit Hit

**Date Opened:** 2024-01-15  
**Date Resolved:** 2024-01-16  
**Severity:** 🟡 Medium  
**Status:** 🟢 Resolved  

**Description:**
Hit 25 calls/day limit on Alpha Vantage API while testing historical data fetch.

**Impact:**
- Blocked testing of `get_historical_data()` method
- Couldn't validate RSI calculation
- Delayed Milestone 2 by 1 day

**Solution:**
1. Implemented response caching (Redis, 24h TTL)
2. Added fallback to Polygon.io for historical data
3. Rate limit tracking in database

**Code Changes:**
- Added `cache_historical_data()` in `market_data.py`
- Modified `get_historical_data()` to check cache first
- Commit: `abc123def`

**Workaround Used:**
Used cached data from previous day while waiting for rate limit reset.

**Prevention:**
- Added daily call counter to STATUS.md
- Alert at 20/25 calls to slow down
- Documentation updated about rate limits

**Time Lost:** 4 hours  
**Lesson Learned:** Always implement caching from day 1 for rate-limited APIs

---

### Blocker #3: [Example - Delete this]

**Date Opened:** YYYY-MM-DD  
**Date Resolved:** YYYY-MM-DD  
**Severity:** 🔴 High  
**Status:** 🟢 Resolved  

[Same format as above]

---

## 📋 KNOWN ISSUES (Not Blockers)

**Issues that don't block progress but should be tracked:**

### Issue #1: PostgreSQL Slow on Large Queries

**Date:** YYYY-MM-DD  
**Severity:** 🟢 Low  
**Priority:** P3 (nice to have)  

**Description:**
Query to fetch 30 days of market data for 10 stocks takes 2-3 seconds.

**Impact:**
Minor - Dashboard feels slightly sluggish.

**Solution Plan:**
- Add database indexes (later)
- Implement pagination
- Not urgent for MVP

**Status:** Acknowledged, will fix in optimization phase

---

## 🔍 INVESTIGATION LOG

**Problems currently being investigated:**

### Investigation #1: [Title]

**Date Started:** YYYY-MM-DD  
**Question:** [What are we trying to figure out?]  

**Hypothesis:**
[What we think the problem might be]

**Tests Done:**
1. [Test 1] - Result: X
2. [Test 2] - Result: Y

**Next Steps:**
- [ ] Try approach A
- [ ] Check documentation for B
- [ ] Ask user about C

**Notes:**
[Research findings, links, etc.]

---

## 🐛 BUGS FOUND

**Non-blocking bugs to fix:**

### Bug #1: Sentiment Score Incorrect for Negative News

**Date Found:** YYYY-MM-DD  
**Severity:** 🟡 Medium  
**Status:** 🟡 Investigating  
**Found In:** `sentiment_data.py:87`  

**Description:**
Sentiment analyzer returns positive score (+0.6) for clearly negative news headline.

**Example:**
- Input: "NVDA stock plummets on earnings miss"
- Expected: Negative score (-0.5 to -0.8)
- Actual: +0.6

**Root Cause:**
Keyword matching too simplistic. Word "stock" is counted as positive.

**Fix Plan:**
1. Use FinBERT sentiment model instead
2. Implement proper NLP analysis
3. Test with 50 sample headlines

**Workaround:**
Manual review of sentiment scores in dashboard.

**Priority:** P2 (should fix before M3)

---

## 💡 TECHNICAL CHALLENGES

**Difficult problems we solved (for future reference):**

### Challenge #1: Multi-Agent Consensus Algorithm

**Date:** YYYY-MM-DD  
**Problem:** How to weight different agent recommendations?

**Attempted Approaches:**
1. **Simple majority** - Too crude, lost nuance
2. **Weighted by confidence** - Overcomplicated
3. **Threshold-based** - Perfect balance ✅

**Final Solution:**
- 4/4 agree = confidence 5 (STRONG BUY)
- 3/4 agree = confidence 4 (BUY)
- 2/4 mixed = confidence 2 (HOLD)

**Why It Works:**
Simple to implement, preserves agent independence, clear signal strength.

**Code Location:** `signal_generator.py:98-115`

---

## 🔧 WORKAROUNDS IN PRODUCTION

**Temporary fixes that need proper solutions later:**

### Workaround #1: Manual API Key Rotation

**Date Implemented:** YYYY-MM-DD  
**Problem:** Alpha Vantage 25 calls/day limit too restrictive

**Temporary Fix:**
Manually switching API keys when limit hit.

**Proper Solution Needed:**
- Automatic key rotation
- Multiple API keys in rotation
- Better caching strategy

**Priority:** P2  
**Plan:** Implement in Milestone 3

---

## 📊 BLOCKER STATISTICS

**Summary:**
- Total blockers encountered: 4
- Average resolution time: ~12 minutes
- Currently open: 0
- Resolved: 4

**By Severity:**
- 🔴 High: 3 resolved, 0 open
- 🟡 Medium: 1 resolved, 0 open
- 🟢 Low: 0 resolved, 0 open

**By Category:**
- API/External: 0
- Code/Logic: 2 (Session 11 - Mock + Timestamp)
- Infrastructure: 0
- Configuration/Dependencies: 2 (Milestone 1 - psycopg, pandas)

**Top Time Wasters:**
1. Python 3.13 package compatibility - 20 minutes total
2. PostgreSQL timestamp comparison - 15 minutes
3. SQLAlchemy mock configuration - 10 minutes

**Last Updated:** 2026-01-04

---

## 🆘 ESCALATION CRITERIA

**When to escalate to user:**

**Immediate Escalation (STOP WORK):**
- 🔴 High severity blocker with no workaround
- Security vulnerability discovered
- Data loss or corruption
- Can't proceed with milestone

**Same-Day Escalation:**
- 🟡 Medium severity, tried 3+ solutions
- Need architectural decision
- API costs exceed budget
- External dependency broken

**Next Session Escalation:**
- 🟢 Low severity
- Question about requirements
- Optimization suggestions

---

## 📝 BLOCKER TEMPLATE

**Use this when adding new blocker:**

```markdown
### Blocker #X: [Short Title]

**Date Opened:** YYYY-MM-DD  
**Severity:** 🔴 High | 🟡 Medium | 🟢 Low  
**Impact:** [What's blocked?]  
**Status:** 🔴 Open  

**Description:**
[Clear explanation]

**Error Message:**
```
[If applicable]
```

**Attempted Solutions:**
1. Tried X - Result
2. Tried Y - Result

**Current Workaround:**
[Or "None"]

**Needs:**
- [ ] [What's needed to resolve]

**Related:**
- Milestone: [X]
- Files: [List]
```

---

## 🎓 LESSONS LEARNED

**General debugging wisdom:**

1. **Always check the logs first**
   - 80% of issues visible in logs
   - Enable verbose logging early

2. **Test with real data**
   - Mock data hides edge cases
   - Use production-like test data

3. **One change at a time**
   - Multiple changes = hard to debug
   - Commit after each fix

4. **Document workarounds**
   - Future you will forget
   - Technical debt accumulates

5. **Ask for help early**
   - Don't waste 4 hours on Google
   - User often has context you lack

---

## 🔗 USEFUL RESOURCES

**Common debugging links:**

**APIs:**
- [Polygon.io Status](https://status.polygon.io/)
- [Finnhub API Docs](https://finnhub.io/docs/api)
- [Alpha Vantage Support](https://www.alphavantage.co/support/)

**Python:**
- [FastAPI Debugging](https://fastapi.tiangolo.com/tutorial/debugging/)
- [SQLAlchemy Common Issues](https://docs.sqlalchemy.org/en/14/faq/)
- [Celery Troubleshooting](https://docs.celeryproject.org/en/stable/userguide/troubleshooting.html)

**Infrastructure:**
- [Docker Debug Guide](https://docs.docker.com/config/containers/logging/)
- [PostgreSQL Common Errors](https://wiki.postgresql.org/wiki/Troubleshooting)

---

**END OF BLOCKERS LOG**

*Add to this file immediately when you hit a problem. Document the journey to solution. Help future you (or next dev) avoid the same issues.*
