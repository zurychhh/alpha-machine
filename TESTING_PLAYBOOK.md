# ALPHA MACHINE - COMPREHENSIVE TESTING PLAYBOOK
## Complete Test Strategy & Execution Guide for Claude Code

**Version:** 1.0  
**Date:** December 21, 2025  
**Purpose:** Ensure 100% system reliability through exhaustive testing  
**Philosophy:** Test everything, test thoroughly, automate completely

---

## 🎯 TESTING PHILOSOPHY

### Core Principles

1. **Test Before Deploy** - Nothing goes to production untested
2. **Test After Every Change** - Code → Test → Commit cycle
3. **Test All Layers** - Unit → Integration → E2E
4. **Test All Scenarios** - Happy path + edge cases + failures
5. **Automate Everything** - Manual tests = technical debt

### Testing Pyramid

```
        ┌─────────────┐
        │   E2E (5%)  │  ← Full system flows
        ├─────────────┤
        │ Integration │  ← Multi-component
        │   (25%)     │
        ├─────────────┤
        │    Unit     │  ← Individual functions
        │   (70%)     │
        └─────────────┘
```

---

## 📋 TEST CATEGORIES

### 1. UNIT TESTS (70% coverage target)

**What:** Test individual functions/methods in isolation  
**When:** After writing any new function  
**Tool:** pytest  
**Location:** `backend/tests/unit/`

**Coverage Requirements:**
- All agent methods: 100%
- All service methods: 90%
- All utility functions: 80%
- API routes: 100%

---

### 2. INTEGRATION TESTS (25% coverage target)

**What:** Test multiple components working together  
**When:** After completing a feature  
**Tool:** pytest with fixtures  
**Location:** `backend/tests/integration/`

**Coverage Requirements:**
- Agent orchestration: 100%
- Data pipeline: 100%
- Database operations: 100%
- API workflows: 100%

---

### 3. END-TO-END TESTS (5% coverage target)

**What:** Test complete user flows  
**When:** Before deployment  
**Tool:** pytest + requests  
**Location:** `backend/tests/e2e/`

**Coverage Requirements:**
- Signal generation flow: 100%
- Portfolio tracking flow: 100%
- Performance reporting: 100%

---

### 4. PERFORMANCE TESTS

**What:** Measure speed, load, resource usage  
**When:** Weekly + before deployment  
**Tool:** pytest-benchmark, locust  
**Location:** `backend/tests/performance/`

**Metrics:**
- Signal generation time: <30 seconds
- API response time: <500ms
- Database query time: <100ms
- Memory usage: <512MB

---

### 5. ERROR HANDLING TESTS

**What:** Verify graceful failure  
**When:** After implementing error handling  
**Tool:** pytest with mocking  
**Location:** `backend/tests/errors/`

**Scenarios:**
- API failures (401, 429, 500)
- Network timeouts
- Invalid data
- Rate limits
- Database errors

---

## 🧪 DETAILED TEST SPECIFICATIONS

### UNIT TESTS

#### 1. Agent Tests (`tests/unit/test_agents.py`)

**Test Each Agent:**

```python
class TestContrarianAgent:
    """Test GPT-4o Contrarian Agent"""
    
    # BASIC FUNCTIONALITY
    def test_agent_initialization(self):
        """Agent initializes with correct name and API key"""
        agent = ContrarianAgent()
        assert agent.name == "contrarian"
        assert agent.model == "gpt-4o"
        
    def test_agent_analyze_returns_valid_format(self):
        """analyze() returns dict with required keys"""
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert "signal" in result
        assert "confidence" in result
        assert "reasoning" in result
        assert "agent" in result
        
    def test_agent_signal_range_valid(self):
        """Signal is between -1.0 and +1.0"""
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert -1.0 <= result["signal"] <= 1.0
        
    def test_agent_confidence_range_valid(self):
        """Confidence is between 0.0 and 1.0"""
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert 0.0 <= result["confidence"] <= 1.0
        
    def test_agent_reasoning_not_empty(self):
        """Reasoning string is not empty"""
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert len(result["reasoning"]) > 0
    
    # DECISION LOGIC
    def test_oversold_negative_sentiment_buy_signal(self):
        """RSI < 30 + negative sentiment → BUY signal"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 25.0}}
        sentiment = {"combined_sentiment": -0.6}
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert result["signal"] > 0.3  # Should be BUY
        
    def test_overbought_positive_sentiment_sell_signal(self):
        """RSI > 70 + positive sentiment → SELL signal"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 75.0}}
        sentiment = {"combined_sentiment": 0.7}
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert result["signal"] < -0.3  # Should be SELL
        
    def test_neutral_conditions_hold_signal(self):
        """Neutral RSI + neutral sentiment → HOLD signal"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 50.0}}
        sentiment = {"combined_sentiment": 0.0}
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert -0.3 <= result["signal"] <= 0.3  # Should be HOLD
    
    # EDGE CASES
    def test_missing_rsi_data_graceful_handling(self):
        """Agent handles missing RSI gracefully"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {}}  # No RSI
        sentiment = {"combined_sentiment": 0.0}
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert "signal" in result  # Should not crash
        
    def test_missing_sentiment_data_graceful_handling(self):
        """Agent handles missing sentiment gracefully"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 50.0}}
        sentiment = {}  # No sentiment
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert "signal" in result  # Should not crash
        
    def test_extreme_rsi_values_clamped(self):
        """RSI > 100 or < 0 handled correctly"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 150.0}}  # Invalid
        sentiment = {"combined_sentiment": 0.0}
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert "signal" in result  # Should handle gracefully
        
    def test_extreme_sentiment_values_clamped(self):
        """Sentiment > 1 or < -1 handled correctly"""
        agent = ContrarianAgent()
        
        market_data = {"indicators": {"rsi": 50.0}}
        sentiment = {"combined_sentiment": 5.0}  # Invalid
        
        result = agent.analyze("NVDA", market_data, sentiment)
        
        assert "signal" in result  # Should handle gracefully
    
    # API FAILURES
    @patch('openai.ChatCompletion.create')
    def test_openai_api_timeout_returns_hold(self, mock_api):
        """Timeout → HOLD signal with confidence 0"""
        mock_api.side_effect = TimeoutError()
        
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert result["signal"] == 0.0
        assert result["confidence"] == 0.0
        
    @patch('openai.ChatCompletion.create')
    def test_openai_api_401_returns_hold(self, mock_api):
        """Invalid API key → HOLD signal + error logged"""
        mock_api.side_effect = AuthenticationError()
        
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert result["signal"] == 0.0
        
    @patch('openai.ChatCompletion.create')
    def test_openai_api_429_returns_hold(self, mock_api):
        """Rate limit → HOLD signal + retry logic"""
        mock_api.side_effect = RateLimitError()
        
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert result["signal"] == 0.0
        
    @patch('openai.ChatCompletion.create')
    def test_openai_api_500_returns_hold(self, mock_api):
        """Server error → HOLD signal + error logged"""
        mock_api.side_effect = InternalServerError()
        
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
        
        assert result["signal"] == 0.0
    
    # DATA VALIDATION
    def test_invalid_ticker_format_rejected(self):
        """Invalid ticker raises ValueError"""
        agent = ContrarianAgent()
        
        with pytest.raises(ValueError):
            agent.analyze("123", mock_market_data, mock_sentiment)
        
    def test_negative_price_rejected(self):
        """Negative price raises ValueError"""
        agent = ContrarianAgent()
        
        market_data = {"current_price": -100.0}
        
        with pytest.raises(ValueError):
            agent.analyze("NVDA", market_data, mock_sentiment)
        
    def test_empty_market_data_handled(self):
        """Empty dict → default values used"""
        agent = ContrarianAgent()
        
        result = agent.analyze("NVDA", {}, mock_sentiment)
        
        assert "signal" in result  # Should not crash
    
    # RESPONSE PARSING
    def test_json_parsing_markdown_cleaned(self):
        """```json wrapper removed correctly"""
        # Test implementation
        
    def test_json_parsing_handles_invalid_json(self):
        """Invalid JSON → HOLD signal"""
        # Test implementation
        
    def test_json_parsing_handles_partial_response(self):
        """Incomplete JSON → HOLD signal"""
        # Test implementation
```

**Repeat for all agents:**
- `TestGrowthAgent` (Claude Sonnet 4)
- `TestMultiModalAgent` (Gemini 2.0)
- `TestPredictorAgent` (Rule-based)

**Test Matrix (per agent):**
```
Total tests per agent: 25
├── Basic functionality: 5 tests
├── Decision logic: 3 tests
├── Edge cases: 4 tests
├── API failures: 4 tests
├── Data validation: 3 tests
└── Response parsing: 3 tests

Total for 4 agents: 100 unit tests
```

---

#### 2. Service Tests (`tests/unit/test_services.py`)

**Market Data Service:**

```python
class TestMarketDataService:
    """Test market data fetching and aggregation"""
    
    # POLYGON.IO
    def test_polygon_get_current_price_valid_ticker(self):
        """Polygon returns valid price for NVDA"""
        service = MarketDataService()
        price = service.get_current_price("NVDA")
        
        assert isinstance(price, float)
        assert price > 0
        
    def test_polygon_get_current_price_invalid_ticker(self):
        """Polygon handles invalid ticker gracefully"""
        service = MarketDataService()
        price = service.get_current_price("INVALID")
        
        assert price is None
        
    @patch('requests.get')
    def test_polygon_rate_limit_fallback_to_finnhub(self, mock_get):
        """429 error → fallback to Finnhub"""
        # First call (Polygon) returns 429
        # Second call (Finnhub) returns valid data
        mock_get.side_effect = [
            MagicMock(status_code=429),
            MagicMock(status_code=200, json=lambda: {"c": 180.50})
        ]
        
        service = MarketDataService()
        price = service.get_current_price("NVDA")
        
        assert price == 180.50
        
    @patch('requests.get')
    def test_polygon_network_timeout_fallback(self, mock_get):
        """Timeout → fallback to Finnhub"""
        mock_get.side_effect = [
            TimeoutError(),
            MagicMock(status_code=200, json=lambda: {"c": 180.50})
        ]
        
        service = MarketDataService()
        price = service.get_current_price("NVDA")
        
        assert price == 180.50
    
    # FINNHUB
    def test_finnhub_get_current_price_valid_ticker(self):
        """Finnhub returns valid price"""
        # Test implementation
        
    def test_finnhub_fallback_to_alpha_vantage(self):
        """Finnhub failure → Alpha Vantage"""
        # Test implementation
    
    # ALPHA VANTAGE
    def test_alpha_vantage_get_historical_data(self):
        """Returns 30 days of OHLCV data"""
        service = MarketDataService()
        data = service.get_historical_data("NVDA", days=30)
        
        assert len(data) == 30
        assert "close" in data[0]
        assert "volume" in data[0]
        
    def test_alpha_vantage_get_technical_indicators(self):
        """Returns RSI, MACD, etc."""
        service = MarketDataService()
        indicators = service.get_technical_indicators("NVDA")
        
        assert "rsi" in indicators
        assert 0 <= indicators["rsi"] <= 100
        
    @patch('requests.get')
    def test_alpha_vantage_rate_limit_cached(self, mock_get):
        """Rate limit → return cached data"""
        # Test implementation
    
    # DATA VALIDATION
    def test_price_data_format_validation(self):
        """Price is float > 0"""
        # Test implementation
        
    def test_historical_data_sorted_by_date(self):
        """Data sorted newest to oldest"""
        # Test implementation
        
    def test_rsi_value_range_valid(self):
        """RSI between 0 and 100"""
        # Test implementation
    
    # CACHING
    def test_data_cached_on_success(self):
        """Successful fetch → stored in cache"""
        # Test implementation
        
    def test_cached_data_returned_on_failure(self):
        """API failure → return cached data if available"""
        # Test implementation
        
    def test_cache_expiry_honored(self):
        """Stale cache (>1hr) not returned"""
        # Test implementation
```

**Sentiment Data Service:**

```python
class TestSentimentDataService:
    """Test sentiment aggregation"""
    
    # REDDIT
    def test_reddit_sentiment_wsb_mentions(self):
        """Returns mention count from r/wallstreetbets"""
        service = SentimentDataService()
        data = service.get_reddit_sentiment("NVDA")
        
        assert "mentions" in data
        assert data["mentions"] >= 0
        
    def test_reddit_sentiment_score_calculation(self):
        """Sentiment score = (positive - negative) / total"""
        # Test implementation
        
    @patch('praw.Reddit')
    def test_reddit_api_failure_returns_zero(self, mock_reddit):
        """Reddit down → sentiment = 0.0"""
        mock_reddit.side_effect = Exception()
        
        service = SentimentDataService()
        data = service.get_reddit_sentiment("NVDA")
        
        assert data["sentiment_score"] == 0.0
    
    # NEWS API
    def test_newsapi_article_fetching(self):
        """Returns recent news articles"""
        # Test implementation
        
    def test_newsapi_sentiment_keyword_analysis(self):
        """Positive/negative keyword detection"""
        # Test implementation
        
    def test_newsapi_rate_limit_handling(self):
        """Rate limit → cached data"""
        # Test implementation
    
    # AGGREGATION
    def test_combined_sentiment_weighted_average(self):
        """Combined = reddit*0.6 + news*0.4"""
        service = SentimentDataService()
        
        # Mock data
        reddit_sentiment = 0.5
        news_sentiment = 0.3
        
        expected = 0.5 * 0.6 + 0.3 * 0.4  # 0.42
        
        # Test calculation
        
    def test_sentiment_score_clamped_to_range(self):
        """Score between -1.0 and +1.0"""
        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA")
        
        assert -1.0 <= result["combined_sentiment"] <= 1.0
```

**Total service tests:** ~40 tests

---

#### 3. Signal Generator Tests (`tests/unit/test_signal_generator.py`)

```python
class TestSignalGenerator:
    """Test multi-agent consensus logic"""
    
    # CONSENSUS ALGORITHM
    def test_all_agents_agree_buy_high_confidence(self):
        """4/4 BUY → signal +0.8, confidence 0.95"""
        generator = SignalGenerator()
        
        agent_votes = [
            {"signal": 0.8, "confidence": 0.9},
            {"signal": 0.7, "confidence": 0.8},
            {"signal": 0.75, "confidence": 0.85},
            {"signal": 0.6, "confidence": 0.7},
        ]
        
        result = generator.calculate_consensus(agent_votes)
        
        assert result["signal"] > 0.6
        assert result["confidence"] > 0.8
        
    def test_all_agents_agree_sell_high_confidence(self):
        """4/4 SELL → signal -0.8, confidence 0.95"""
        # Test implementation
        
    def test_majority_buy_medium_confidence(self):
        """3/4 BUY → signal +0.5, confidence 0.75"""
        # Test implementation
        
    def test_split_decision_low_confidence(self):
        """2 BUY, 2 SELL → signal ~0, confidence 0.3"""
        generator = SignalGenerator()
        
        agent_votes = [
            {"signal": 0.6, "confidence": 0.7},
            {"signal": 0.5, "confidence": 0.6},
            {"signal": -0.6, "confidence": 0.7},
            {"signal": -0.5, "confidence": 0.6},
        ]
        
        result = generator.calculate_consensus(agent_votes)
        
        assert -0.2 <= result["signal"] <= 0.2
        assert result["confidence"] < 0.5
    
    # WEIGHTING
    def test_agent_weights_applied_correctly(self):
        """Contrarian weight 1.2 > others 1.0"""
        # Test implementation
        
    def test_higher_weight_agent_influences_more(self):
        """Contrarian vote counts 20% more"""
        # Test implementation
    
    # POSITION SIZING
    def test_position_size_scales_with_confidence(self):
        """High confidence → larger position"""
        generator = SignalGenerator()
        
        high_conf = generator.calculate_position_size(price=100, confidence=0.9)
        low_conf = generator.calculate_position_size(price=100, confidence=0.3)
        
        assert high_conf > low_conf
        
    def test_position_size_respects_max_limit(self):
        """Never exceed 10% of capital"""
        generator = SignalGenerator()
        
        size = generator.calculate_position_size(price=50, confidence=1.0)
        max_allowed = 50000 * 0.10  # $50k capital * 10%
        
        assert size * 50 <= max_allowed
        
    def test_position_size_zero_on_hold_signal(self):
        """HOLD signal → position_size = 0"""
        generator = SignalGenerator()
        
        size = generator.calculate_position_size(price=100, confidence=0.0)
        
        assert size == 0
    
    # RISK PARAMETERS
    def test_stop_loss_set_correctly(self):
        """Stop loss = entry_price * 0.90"""
        generator = SignalGenerator()
        
        entry_price = 100.0
        stop_loss = generator.calculate_stop_loss(entry_price)
        
        assert stop_loss == 90.0
        
    def test_take_profit_levels_calculated(self):
        """TP1 = +25%, TP2 = +50%, TP3 = +100%"""
        generator = SignalGenerator()
        
        entry_price = 100.0
        targets = generator.calculate_take_profit_levels(entry_price)
        
        assert targets["tp1"] == 125.0
        assert targets["tp2"] == 150.0
        assert targets["tp3"] == 200.0
    
    # ERROR HANDLING
    @patch('app.agents.contrarian_agent.ContrarianAgent.analyze')
    def test_single_agent_failure_continues(self, mock_analyze):
        """1 agent fails → continue with 3 agents"""
        mock_analyze.side_effect = Exception()
        
        generator = SignalGenerator()
        result = generator.generate_signal("NVDA", mock_db)
        
        assert result is not None  # Should not crash
        
    @patch.multiple(
        'app.agents',
        ContrarianAgent=MagicMock(side_effect=Exception),
        GrowthAgent=MagicMock(side_effect=Exception),
        MultiModalAgent=MagicMock(side_effect=Exception),
        PredictorAgent=MagicMock(side_effect=Exception),
    )
    def test_all_agents_fail_returns_hold(self):
        """All fail → HOLD signal, confidence 0"""
        generator = SignalGenerator()
        result = generator.generate_signal("NVDA", mock_db)
        
        assert result["signal_type"] == "HOLD"
        assert result["confidence"] == 0
```

**Total signal generator tests:** ~25 tests

---

### INTEGRATION TESTS

#### 1. Multi-Agent Integration (`tests/integration/test_multi_agent.py`)

```python
class TestMultiAgentIntegration:
    """Test agents working together"""
    
    def test_all_agents_analyze_same_ticker(self):
        """All 4 agents analyze NVDA without conflicts"""
        agents = [
            ContrarianAgent(),
            GrowthAgent(),
            MultiModalAgent(),
            PredictorAgent(),
        ]
        
        results = []
        for agent in agents:
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment)
            results.append(result)
        
        assert len(results) == 4
        assert all("signal" in r for r in results)
        
    def test_agents_return_different_perspectives(self):
        """Agents have different signals (diversity check)"""
        # Run all agents
        # Check that signals vary (not all identical)
        
    def test_consensus_aggregates_all_votes(self):
        """Signal generator uses all 4 agent outputs"""
        # Test implementation
        
    def test_parallel_agent_execution_completes(self):
        """All agents run concurrently, finish in <30s"""
        # Test implementation
```

---

#### 2. Data Pipeline Integration (`tests/integration/test_data_pipeline.py`)

```python
class TestDataPipeline:
    """Test end-to-end data flow"""
    
    def test_market_data_flows_to_agents(self):
        """Polygon → agents receive correct data"""
        # Fetch real market data
        # Pass to agent
        # Verify agent receives data
        
    def test_sentiment_data_flows_to_agents(self):
        """NewsAPI → agents receive sentiment"""
        # Test implementation
        
    def test_database_stores_fetched_data(self):
        """Market data saved to PostgreSQL"""
        # Test implementation
        
    def test_cached_data_reused_on_subsequent_calls(self):
        """Second call uses cache (faster)"""
        # Test implementation
```

---

#### 3. API Integration (`tests/integration/test_api.py`)

```python
class TestAPIIntegration:
    """Test API endpoints end-to-end"""
    
    def test_generate_signal_endpoint_full_flow(self):
        """POST /signals/generate/NVDA → complete signal"""
        response = client.post("/api/v1/signals/generate/NVDA")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "signal_type" in data
        assert "confidence" in data
        assert "agent_votes" in data
        
    def test_get_signals_endpoint_returns_list(self):
        """GET /signals → all generated signals"""
        # Test implementation
        
    def test_get_signal_by_id_returns_details(self):
        """GET /signals/1 → signal + agent analyses"""
        # Test implementation
```

---

### END-TO-END TESTS

#### 1. Signal Generation Flow (`tests/e2e/test_signal_flow.py`)

```python
class TestSignalGenerationE2E:
    """Test complete user flow: request → signal → database"""
    
    @pytest.mark.slow
    def test_complete_signal_generation_nvda(self):
        """
        Full flow test:
        1. User requests signal for NVDA
        2. System fetches market data (Polygon)
        3. System fetches sentiment (NewsAPI)
        4. All 4 agents analyze
        5. Consensus calculated
        6. Signal stored in database
        7. Response returned to user
        
        Verify:
        - Response has all required fields
        - Database has new signal row
        - Database has 4 agent_analysis rows
        - Timing < 30 seconds
        """
        import time
        
        start_time = time.time()
        
        # Make request
        response = client.post("/api/v1/signals/generate/NVDA")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "signal_type" in data
        assert "confidence" in data
        
        # Verify database
        signal_id = data["id"]
        
        # Check signal exists
        signal = db.query(Signal).filter(Signal.id == signal_id).first()
        assert signal is not None
        
        # Check 4 agent analyses exist
        analyses = db.query(AgentAnalysis).filter(
            AgentAnalysis.signal_id == signal_id
        ).all()
        assert len(analyses) == 4
        
        # Verify timing
        assert duration < 30.0  # Must complete in <30 seconds
        
    def test_multiple_signals_different_tickers(self):
        """Generate signals for 5 stocks sequentially"""
        tickers = ["NVDA", "MSFT", "GOOGL", "AMD", "PLTR"]
        
        for ticker in tickers:
            response = client.post(f"/api/v1/signals/generate/{ticker}")
            assert response.status_code == 200
        
    def test_signal_persistence_across_restarts(self):
        """Signal accessible after server restart"""
        # Generate signal
        response = client.post("/api/v1/signals/generate/NVDA")
        signal_id = response.json()["id"]
        
        # Simulate server restart (clear cache, etc.)
        
        # Fetch signal again
        response = client.get(f"/api/v1/signals/{signal_id}")
        assert response.status_code == 200
```

---

#### 2. Portfolio Tracking Flow (`tests/e2e/test_portfolio_flow.py`)

```python
class TestPortfolioTrackingE2E:
    """Test portfolio management end-to-end"""
    
    def test_paper_trade_execution_flow(self):
        """
        Full flow:
        1. Generate BUY signal for NVDA
        2. Execute paper trade
        3. Verify position added to portfolio
        4. Verify P&L calculation
        5. Verify performance tracking
        """
        # Test implementation
        
    def test_multiple_positions_portfolio_value(self):
        """Hold 3 positions → correct total value"""
        # Test implementation
```

---

### PERFORMANCE TESTS

#### 1. Response Time Tests (`tests/performance/test_response_time.py`)

```python
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

class TestResponseTime:
    """Measure critical path latency"""
    
    def test_single_agent_response_time(self, benchmark: BenchmarkFixture):
        """Single agent analysis < 5 seconds"""
        agent = ContrarianAgent()
        
        result = benchmark(
            agent.analyze, 
            "NVDA", 
            mock_market_data, 
            mock_sentiment
        )
        
        # Benchmark will fail if exceeds threshold
        assert benchmark.stats.mean < 5.0
        
    def test_all_agents_parallel_response_time(self, benchmark: BenchmarkFixture):
        """4 agents parallel < 10 seconds"""
        # Test implementation
        
    def test_signal_generation_total_time(self, benchmark: BenchmarkFixture):
        """Full signal generation < 30 seconds"""
        # Test implementation
        
    def test_api_endpoint_response_time(self, benchmark: BenchmarkFixture):
        """API response < 500ms (cached data)"""
        # Test implementation
```

---

#### 2. Load Tests (`tests/performance/test_load.py`)

```python
class TestLoadHandling:
    """Test system under load"""
    
    def test_10_concurrent_requests(self):
        """System handles 10 simultaneous signals"""
        import concurrent.futures
        
        def generate_signal(ticker):
            return client.post(f"/api/v1/signals/generate/{ticker}")
        
        tickers = ["NVDA"] * 10
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_signal, t) for t in tickers]
            results = [f.result() for f in futures]
        
        assert all(r.status_code == 200 for r in results)
        
    def test_100_requests_sequential(self):
        """System processes 100 signals sequentially"""
        # Test implementation
        
    def test_database_connection_pool(self):
        """Connection pool handles concurrent queries"""
        # Test implementation
```

---

### ERROR HANDLING TESTS

#### 1. API Failure Tests (`tests/errors/test_api_failures.py`)

```python
class TestAPIFailures:
    """Test resilience to external API failures"""
    
    @patch('requests.get')
    def test_polygon_503_fallback_to_finnhub(self, mock_get):
        """Polygon down → Finnhub used"""
        # Mock Polygon 503
        # Mock Finnhub 200
        # Verify fallback worked
        
    @patch('requests.get')
    def test_all_market_apis_down_use_cache(self, mock_get):
        """All APIs down → return cached data"""
        # Test implementation
        
    @patch('openai.ChatCompletion.create')
    def test_openai_rate_limit_agent_skip(self, mock_api):
        """OpenAI 429 → skip agent, continue with 3"""
        # Test implementation
        
    @patch('anthropic.Anthropic.messages.create')
    def test_anthropic_timeout_agent_skip(self, mock_api):
        """Claude timeout → skip agent"""
        # Test implementation
```

---

#### 2. Data Validation Tests (`tests/errors/test_data_validation.py`)

```python
class TestDataValidation:
    """Test invalid data handling"""
    
    def test_invalid_ticker_format_rejected(self):
        """Ticker '123' → ValueError"""
        with pytest.raises(ValueError):
            validate_ticker("123")
        
    def test_negative_price_rejected(self):
        """Price -100 → ValueError"""
        with pytest.raises(ValueError):
            validate_price(-100.0)
        
    def test_rsi_out_of_range_clamped(self):
        """RSI 150 → clamped to 100"""
        result = clamp_rsi(150.0)
        assert result == 100.0
```

---

## 🎯 TEST EXECUTION STRATEGY

### Daily Testing (Developer)

```bash
# Quick smoke test (1 minute)
pytest tests/unit/test_agents.py::TestContrarianAgent -v

# Before commit (3 minutes)
pytest tests/unit/ -v --tb=short

# Before push (10 minutes)
pytest tests/unit/ tests/integration/ -v
```

---

### Pre-Deployment Testing (Full Suite)

```bash
# Complete test suite (30 minutes)
pytest --cov=app --cov-report=html --cov-report=term

# Performance tests
pytest tests/performance/ -v --benchmark-only

# E2E tests
pytest tests/e2e/ -v --tb=short

# Generate reports
pytest --html=test-report.html --self-contained-html
```

---

### Continuous Integration (GitHub Actions)

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-benchmark
      
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app
      
      - name: Run integration tests
        run: pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📊 TEST COVERAGE REQUIREMENTS

### Minimum Coverage Targets

```
Overall:        80%
├── Agents:     100% (critical path)
├── Services:   90%  (data integrity)
├── API:        100% (user-facing)
├── Utils:      80%  (helpers)
└── Models:     70%  (ORM)
```

### Coverage Commands

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View in browser
open htmlcov/index.html

# Check if meets minimum
pytest --cov=app --cov-fail-under=80
```

---

## 🔍 TEST DATA & FIXTURES

### Conftest.py (Shared Fixtures)

```python
# tests/conftest.py

import pytest
from app.core.database import Base, engine, SessionLocal
from app.models import Signal, AgentAnalysis, Watchlist

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Provide database session for tests"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture
def mock_market_data():
    """Standard market data for testing"""
    return {
        "current_price": 180.50,
        "historical": [
            {"date": "2025-12-20", "close": 179.00, "volume": 1000000},
            # ... 30 days
        ],
        "indicators": {
            "rsi": 55.3,
            "macd": 2.1,
        }
    }

@pytest.fixture
def oversold_market_data():
    """Market data with oversold conditions"""
    return {
        "current_price": 150.00,
        "indicators": {"rsi": 25.0}
    }

@pytest.fixture
def overbought_market_data():
    """Market data with overbought conditions"""
    return {
        "current_price": 200.00,
        "indicators": {"rsi": 75.0}
    }

@pytest.fixture
def mock_sentiment():
    """Standard sentiment data"""
    return {
        "combined_sentiment": 0.5,
        "reddit": {"mentions": 100, "sentiment_score": 0.6},
        "news": {"article_count": 10, "sentiment_score": 0.4}
    }
```

---

## 🚨 TESTING BEST PRACTICES

### 1. Test Isolation

**DO:**
```python
def test_agent_with_fresh_instance():
    agent = ContrarianAgent()  # New instance each test
    result = agent.analyze(...)
    assert result["signal"] > 0
```

**DON'T:**
```python
# BAD: Shared state between tests
agent = ContrarianAgent()  # Module level

def test_one():
    agent.analyze(...)

def test_two():
    agent.analyze(...)  # Might be affected by test_one
```

---

### 2. Arrange-Act-Assert Pattern

```python
def test_consensus_calculation():
    # ARRANGE - Setup test data
    agent_votes = [
        {"signal": 0.8, "confidence": 0.9},
        {"signal": 0.6, "confidence": 0.8},
    ]
    
    # ACT - Execute the code being tested
    result = calculate_consensus(agent_votes)
    
    # ASSERT - Verify the outcome
    assert result["signal"] > 0.6
    assert result["confidence"] > 0.8
```

---

### 3. Mock External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_agent_with_mocked_openai_api():
    """Don't call real APIs in unit tests"""
    
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = mock_response
        
        agent = ContrarianAgent()
        result = agent.analyze("NVDA", market_data, sentiment_data)
        
        assert mock_openai.called
        assert result["signal"] is not None
```

---

## 📈 TEST METRICS & REPORTING

### Key Metrics to Track

```
1. Test Count:          200+ tests
2. Coverage:            80%+ overall
3. Pass Rate:           100% (no failures)
4. Execution Time:      <30 min full suite
5. Flaky Tests:         0 (deterministic only)
6. Code Quality:        A grade (pylint/flake8)
```

---

## 🎓 TESTING CHECKLIST

### Before Committing Code

- [ ] All new functions have unit tests
- [ ] All tests pass locally
- [ ] Coverage maintained (>80%)
- [ ] No commented-out tests
- [ ] No skipped tests without reason
- [ ] Test names are descriptive
- [ ] Docstrings explain what's tested

---

### Before Deploying

- [ ] Full test suite passes
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Performance tests pass
- [ ] Manual smoke test completed
- [ ] Test coverage report reviewed
- [ ] No critical bugs in backlog

---

## 📚 COMPLETE TEST FILE STRUCTURE

```
backend/tests/
├── __init__.py
├── conftest.py               # Shared fixtures
├── pytest.ini                # Pytest configuration
│
├── unit/
│   ├── __init__.py
│   ├── test_agents.py        # 100 tests (25 per agent)
│   ├── test_services.py      # 40 tests (market + sentiment)
│   ├── test_signal_generator.py  # 25 tests
│   ├── test_models.py        # 20 tests
│   └── test_utils.py         # 15 tests
│
├── integration/
│   ├── __init__.py
│   ├── test_multi_agent.py   # 10 tests
│   ├── test_data_pipeline.py # 15 tests
│   ├── test_api.py           # 20 tests
│   └── test_database.py      # 10 tests
│
├── e2e/
│   ├── __init__.py
│   ├── test_signal_flow.py   # 5 tests
│   └── test_portfolio_flow.py # 5 tests
│
├── performance/
│   ├── __init__.py
│   ├── test_response_time.py # 10 tests
│   └── test_load.py          # 5 tests
│
└── errors/
    ├── __init__.py
    ├── test_api_failures.py  # 15 tests
    └── test_data_validation.py # 10 tests
```

**Total Test Count:** 265 tests minimum

---

## 🎯 SUCCESS CRITERIA

**System is fully tested when:**

✅ 265+ tests implemented  
✅ 80%+ code coverage  
✅ 100% tests passing  
✅ <30 min full suite execution  
✅ 0 flaky tests  
✅ All critical paths covered  
✅ Test documentation complete  

---

**END OF TESTING PLAYBOOK**

*Test everything. Test thoroughly. Test automatically. Ship with confidence.*
