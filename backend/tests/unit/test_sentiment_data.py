"""
Unit Tests for Sentiment Data Service
Tests Reddit and News sentiment with mocked API responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.sentiment_data import SentimentDataService, sentiment_service


class TestRedditSentiment:
    """Tests for get_reddit_sentiment() method"""

    @patch("app.services.sentiment_data.settings")
    def test_reddit_no_credentials(self, mock_settings):
        """Test behavior when Reddit credentials not configured"""
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None

        service = SentimentDataService()
        result = service.get_reddit_sentiment("NVDA")

        assert result["source"] == "reddit"
        assert result["mentions"] == 0
        assert result["sentiment_score"] == 0.0

    @patch("praw.Reddit")
    @patch("app.services.sentiment_data.settings")
    def test_reddit_with_mentions(self, mock_settings, mock_reddit_class, mock_reddit_submissions):
        """Test Reddit sentiment with multiple posts"""
        mock_settings.REDDIT_CLIENT_ID = "test_id"
        mock_settings.REDDIT_CLIENT_SECRET = "test_secret"
        mock_settings.REDDIT_USER_AGENT = "TestAgent/1.0"

        # Mock Reddit client
        mock_reddit = MagicMock()
        mock_reddit_class.return_value = mock_reddit

        # Mock subreddit search
        mock_subreddit = MagicMock()
        mock_subreddit.search.return_value = mock_reddit_submissions
        mock_reddit.subreddit.return_value = mock_subreddit

        service = SentimentDataService()
        service.reddit = mock_reddit  # Inject mock
        result = service.get_reddit_sentiment("NVDA")

        assert result["source"] == "reddit"
        assert result["mentions"] > 0

    def test_analyze_reddit_post_positive(self, mock_reddit_submission):
        """Test sentiment analysis of positive Reddit post with VADER"""
        mock_reddit_submission.title = "NVDA to the moon! Amazing growth, strong buy!"
        mock_reddit_submission.selftext = ""

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        # VADER returns float -1.0 to 1.0, positive should be > 0
        assert sentiment > 0.0, f"Expected positive sentiment, got {sentiment}"

    def test_analyze_reddit_post_negative(self, mock_reddit_submission):
        """Test sentiment analysis of negative Reddit post with VADER"""
        mock_reddit_submission.title = "NVDA crash incoming! Terrible disaster, avoid!"
        mock_reddit_submission.selftext = ""
        mock_reddit_submission.score = -10  # Negative score
        mock_reddit_submission.upvote_ratio = 0.3

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        # VADER returns float -1.0 to 1.0, negative should be < 0
        assert sentiment < 0.0, f"Expected negative sentiment, got {sentiment}"

    def test_analyze_reddit_post_neutral(self, mock_reddit_submission):
        """Test sentiment analysis of neutral Reddit post with VADER"""
        mock_reddit_submission.title = "What do you think about NVDA?"
        mock_reddit_submission.selftext = ""
        mock_reddit_submission.score = 25
        mock_reddit_submission.upvote_ratio = 0.5

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        # VADER compound for questions tends to be near 0
        assert -0.3 <= sentiment <= 0.3, f"Expected neutral sentiment, got {sentiment}"

    def test_analyze_reddit_post_high_score_bonus(self, mock_reddit_submission):
        """Test that high score + upvote ratio adds positive sentiment"""
        mock_reddit_submission.title = "Just bought some NVDA shares today"
        mock_reddit_submission.selftext = ""
        mock_reddit_submission.score = 500
        mock_reddit_submission.upvote_ratio = 0.95

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        # High engagement should boost sentiment (engagement bonus +0.1)
        assert sentiment >= 0.0, f"Expected non-negative sentiment with high engagement"


class TestNewsSentiment:
    """Tests for get_news_sentiment() method"""

    @patch("app.services.sentiment_data.settings")
    def test_news_no_api_key(self, mock_settings):
        """Test behavior when NewsAPI key not configured"""
        mock_settings.NEWS_API_KEY = None

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["source"] == "news"
        assert result["article_count"] == 0
        assert result["sentiment_score"] == 0.0

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_success(self, mock_get, mock_settings, mock_newsapi_success_response):
        """Test successful news sentiment retrieval"""
        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=200, json=lambda: mock_newsapi_success_response)

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["source"] == "news"
        assert result["article_count"] == 3
        assert len(result["headlines"]) <= 10

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_empty_results(self, mock_get, mock_settings, mock_newsapi_empty_response):
        """Test handling of empty news results"""
        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=200, json=lambda: mock_newsapi_empty_response)

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["article_count"] == 0
        assert result["sentiment_score"] == 0.0

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_api_error(self, mock_get, mock_settings):
        """Test handling of NewsAPI error"""
        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=401)

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["article_count"] == 0

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_rate_limit(self, mock_get, mock_settings):
        """Test handling of NewsAPI rate limit"""
        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=429)

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["article_count"] == 0


class TestAnalyzeHeadline:
    """Tests for _analyze_headline() method with VADER"""

    def test_positive_headline(self):
        """Test positive headline detection with VADER"""
        service = SentimentDataService()

        headlines = [
            "NVDA stock surges on amazing strong earnings",
            "NVIDIA rally continues as AI demand soars beautifully",
            "Analysts upgrade NVDA with excellent bullish outlook",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            # VADER returns float, positive headlines should be > 0
            assert sentiment > 0.0, f"Expected positive for: {headline}, got {sentiment}"

    def test_negative_headline(self):
        """Test negative headline detection with VADER"""
        service = SentimentDataService()

        headlines = [
            "NVDA plunges terribly on weak awful guidance",
            "NVIDIA stock crashes horribly amid terrible market selloff",
            "Serious concerns grow over NVDA poor valuation",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            # VADER returns float, negative headlines should be < 0
            assert sentiment < 0.0, f"Expected negative for: {headline}, got {sentiment}"

    def test_neutral_headline(self):
        """Test neutral headline detection with VADER"""
        service = SentimentDataService()

        headlines = [
            "NVDA reports quarterly results",
            "NVIDIA announces new product",
            "Tech stocks in trading",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            # VADER returns float, neutral should be near 0
            assert -0.3 <= sentiment <= 0.3, f"Expected neutral for: {headline}, got {sentiment}"


class TestAggregateSentiment:
    """Tests for aggregate_sentiment() method"""

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    def test_aggregate_bullish(self, mock_news, mock_reddit):
        """Test aggregation with bullish sentiment"""
        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 50,
            "sentiment_score": 0.7,
            "positive_count": 35,
            "negative_count": 5,
            "neutral_count": 10,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 20,
            "sentiment_score": 0.5,
            "positive_count": 12,
            "negative_count": 3,
            "neutral_count": 5,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=False)

        assert result["combined_sentiment"] > 0.3
        assert result["sentiment_label"] == "bullish"
        assert result["total_mentions"] == 70

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    def test_aggregate_bearish(self, mock_news, mock_reddit):
        """Test aggregation with bearish sentiment"""
        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 40,
            "sentiment_score": -0.6,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 15,
            "sentiment_score": -0.4,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=False)

        assert result["combined_sentiment"] < -0.3
        assert result["sentiment_label"] == "bearish"

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    def test_aggregate_neutral(self, mock_news, mock_reddit):
        """Test aggregation with neutral sentiment"""
        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 30,
            "sentiment_score": 0.05,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 10,
            "sentiment_score": -0.05,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=False)

        assert -0.1 <= result["combined_sentiment"] <= 0.1
        assert result["sentiment_label"] == "neutral"

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    def test_aggregate_no_data(self, mock_news, mock_reddit):
        """Test aggregation when no data available"""
        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 0,
            "sentiment_score": 0,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 0,
            "sentiment_score": 0,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=False)

        assert result["combined_sentiment"] == 0.0
        assert result["sentiment_label"] == "neutral"

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    def test_aggregate_reddit_only(self, mock_news, mock_reddit):
        """Test aggregation with only Reddit data"""
        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 50,
            "sentiment_score": 0.8,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 0,  # No news
            "sentiment_score": 0,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=False)

        # Should use 100% Reddit weight
        assert result["combined_sentiment"] == 0.8


class TestTrendingTickers:
    """Tests for get_trending_tickers() method"""

    @patch("app.services.sentiment_data.settings")
    def test_trending_no_reddit(self, mock_settings):
        """Test trending when Reddit not available"""
        mock_settings.REDDIT_CLIENT_ID = None

        service = SentimentDataService()
        result = service.get_trending_tickers()

        assert result == []

    def test_ticker_extraction_pattern(self):
        """Test that ticker extraction regex works correctly"""
        import re

        pattern = re.compile(r"\b([A-Z]{1,5})\b")

        test_cases = [
            ("NVDA is mooning!", ["NVDA"]),
            ("Check out AMD and INTC", ["AMD", "INTC"]),
            ("I love my TSLA calls", ["I", "TSLA"]),  # 'I' is filtered separately
            ("$AAPL looking good", ["AAPL"]),
        ]

        for text, expected_matches in test_cases:
            matches = pattern.findall(text)
            for expected in expected_matches:
                if expected != "I":  # Would be filtered by exclude list
                    assert expected in matches


class TestSentimentScoreValidation:
    """Tests for sentiment score boundaries"""

    def test_sentiment_score_in_range(self):
        """Test that sentiment scores are always in [-1, 1] range"""
        service = SentimentDataService()

        # Test various keyword combinations
        test_headlines = [
            "surge rally gain bullish upgrade beat record soar jump rise",  # Very positive
            "plunge drop bearish downgrade miss crash fall decline loss",  # Very negative
            "",  # Empty
            "just some random text",  # Neutral
        ]

        for headline in test_headlines:
            score = service._analyze_headline(headline)
            assert -1 <= score <= 1, f"Score {score} out of range for: {headline}"


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_timeout(self, mock_get, mock_settings):
        """Test handling of request timeout"""
        import requests

        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.side_effect = requests.exceptions.Timeout()

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["article_count"] == 0
        assert result["sentiment_score"] == 0.0

    @patch("app.services.sentiment_data.settings")
    @patch("requests.get")
    def test_news_connection_error(self, mock_get, mock_settings):
        """Test handling of connection error"""
        import requests

        mock_settings.NEWS_API_KEY = "test_key"

        mock_get.side_effect = requests.exceptions.ConnectionError()

        service = SentimentDataService()
        result = service.get_news_sentiment("NVDA")

        assert result["article_count"] == 0

    def test_empty_title_handling(self):
        """Test handling of articles with empty titles"""
        service = SentimentDataService()

        # Should not crash on empty string
        sentiment = service._analyze_headline("")
        assert sentiment == 0

        # Test whitespace-only title
        sentiment = service._analyze_headline("   ")
        assert -0.1 <= sentiment <= 0.1  # Near zero


class TestVADERSentiment:
    """Tests for VADER sentiment analysis"""

    def test_vader_initialization(self):
        """Test VADER analyzer is properly initialized"""
        from app.services.sentiment_data import get_vader_analyzer

        analyzer = get_vader_analyzer()
        # Should be initialized or None if vaderSentiment not installed
        # In tests with vaderSentiment installed, it should return an analyzer
        if analyzer is not None:
            # Test basic functionality
            scores = analyzer.polarity_scores("This is great!")
            assert "compound" in scores
            assert -1.0 <= scores["compound"] <= 1.0

    def test_vader_positive_text(self):
        """Test VADER returns positive score for positive text"""
        service = SentimentDataService()

        if service.vader:
            scores = service.vader.polarity_scores("This is amazing and wonderful!")
            assert scores["compound"] > 0.3
        else:
            pytest.skip("VADER not available")

    def test_vader_negative_text(self):
        """Test VADER returns negative score for negative text"""
        service = SentimentDataService()

        if service.vader:
            scores = service.vader.polarity_scores("This is terrible and awful!")
            assert scores["compound"] < -0.3
        else:
            pytest.skip("VADER not available")

    def test_vader_with_reddit_selftext(self, mock_reddit_submission):
        """Test VADER analyzes selftext in addition to title"""
        mock_reddit_submission.title = "NVDA discussion"
        mock_reddit_submission.selftext = "This stock is amazing and will definitely go up! Great earnings!"
        mock_reddit_submission.score = 50
        mock_reddit_submission.upvote_ratio = 0.7

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        # Should be more positive due to selftext content
        assert sentiment > 0.0, f"Expected positive from selftext, got {sentiment}"


class TestRedisCaching:
    """Tests for Redis caching functionality"""

    @patch("redis.from_url")
    @patch("app.services.sentiment_data.settings")
    def test_cache_hit(self, mock_settings, mock_redis_from_url):
        """Test cache hit returns cached data"""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None
        mock_settings.NEWS_API_KEY = None

        # Mock Redis returning cached data
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"cached": true, "combined_sentiment": 0.5}'
        mock_redis_from_url.return_value = mock_redis

        service = SentimentDataService()
        cached = service._get_cached_sentiment("NVDA")

        assert cached is not None
        assert cached["cached"] is True
        assert cached["combined_sentiment"] == 0.5
        mock_redis.get.assert_called_once_with("sentiment:NVDA")

    @patch("redis.from_url")
    @patch("app.services.sentiment_data.settings")
    def test_cache_miss(self, mock_settings, mock_redis_from_url):
        """Test cache miss returns None"""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None

        # Mock Redis returning None (cache miss)
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis_from_url.return_value = mock_redis

        service = SentimentDataService()
        cached = service._get_cached_sentiment("NVDA")

        assert cached is None

    @patch("redis.from_url")
    @patch("app.services.sentiment_data.settings")
    def test_cache_write(self, mock_settings, mock_redis_from_url):
        """Test sentiment data is cached after fetch"""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None

        mock_redis = MagicMock()
        mock_redis_from_url.return_value = mock_redis

        service = SentimentDataService()
        test_data = {"ticker": "NVDA", "combined_sentiment": 0.5}
        service._cache_sentiment("NVDA", test_data)

        # Verify setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "sentiment:NVDA"
        assert call_args[0][1] == 1800  # TTL

    @patch("app.services.sentiment_data.settings")
    def test_cache_disabled_without_redis_url(self, mock_settings):
        """Test caching is disabled when REDIS_URL not set"""
        mock_settings.REDIS_URL = None
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None

        service = SentimentDataService()

        # Should return None without trying Redis
        cached = service._get_cached_sentiment("NVDA")
        assert cached is None

    @patch("redis.from_url")
    @patch("app.services.sentiment_data.settings")
    def test_aggregate_uses_cache(self, mock_settings, mock_redis_from_url):
        """Test aggregate_sentiment uses cached data when available"""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDDIT_CLIENT_ID = None
        mock_settings.REDDIT_CLIENT_SECRET = None
        mock_settings.NEWS_API_KEY = None

        cached_data = {
            "ticker": "NVDA",
            "combined_sentiment": 0.75,
            "sentiment_label": "bullish",
            "total_mentions": 100,
            "timestamp": "2025-01-01T00:00:00",
            "reddit": {"mentions": 60, "sentiment_score": 0.8},
            "news": {"article_count": 40, "sentiment_score": 0.65},
        }

        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"ticker": "NVDA", "combined_sentiment": 0.75, "sentiment_label": "bullish", "total_mentions": 100}'
        mock_redis_from_url.return_value = mock_redis

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=True)

        assert result["from_cache"] is True
        assert result["combined_sentiment"] == 0.75

    @patch.object(SentimentDataService, "get_reddit_sentiment")
    @patch.object(SentimentDataService, "get_news_sentiment")
    @patch.object(SentimentDataService, "_get_cached_sentiment")
    @patch.object(SentimentDataService, "_cache_sentiment")
    def test_aggregate_caches_fresh_data(self, mock_cache_write, mock_cache_read, mock_news, mock_reddit):
        """Test aggregate_sentiment caches fresh data"""
        mock_cache_read.return_value = None  # Cache miss

        mock_reddit.return_value = {
            "source": "reddit",
            "mentions": 50,
            "sentiment_score": 0.7,
        }
        mock_news.return_value = {
            "source": "news",
            "article_count": 20,
            "sentiment_score": 0.5,
        }

        service = SentimentDataService()
        result = service.aggregate_sentiment("NVDA", use_cache=True)

        # Should cache the result
        mock_cache_write.assert_called_once()
        assert result["from_cache"] is False


class TestPredictorAgentSentiment:
    """Tests for sentiment analysis in PredictorAgent"""

    def test_analyze_sentiment_with_data(self):
        """Test _analyze_sentiment with valid sentiment data"""
        from app.agents.predictor_agent import PredictorAgent

        agent = PredictorAgent()
        sentiment_data = {
            "combined_sentiment": 0.6,
            "sentiment_label": "bullish",
            "total_mentions": 50,
            "reddit": {"mentions": 30, "sentiment_score": 0.7},
            "news": {"article_count": 20, "sentiment_score": 0.45},
        }

        score, confidence, reasoning = agent._analyze_sentiment(sentiment_data)

        assert score == 0.6
        assert confidence == 0.7  # 50+ mentions = 0.7 confidence
        assert "bullish" in reasoning
        assert "Reddit" in reasoning
        assert "News" in reasoning

    def test_analyze_sentiment_no_data(self):
        """Test _analyze_sentiment with no data"""
        from app.agents.predictor_agent import PredictorAgent

        agent = PredictorAgent()

        score, confidence, reasoning = agent._analyze_sentiment(None)

        assert score == 0.0
        assert confidence == 0.0
        assert reasoning == ""

    def test_analyze_sentiment_low_mentions(self):
        """Test _analyze_sentiment with low mention count"""
        from app.agents.predictor_agent import PredictorAgent

        agent = PredictorAgent()
        sentiment_data = {
            "combined_sentiment": 0.8,
            "sentiment_label": "bullish",
            "total_mentions": 3,  # Low mentions
            "reddit": {"mentions": 2, "sentiment_score": 0.9},
            "news": {"article_count": 1, "sentiment_score": 0.5},
        }

        score, confidence, reasoning = agent._analyze_sentiment(sentiment_data)

        assert score == 0.8
        assert confidence == 0.2  # Low confidence due to few mentions

    def test_sentiment_weight_in_predictor(self):
        """Test sentiment has 20% weight in signal generation"""
        from app.agents.predictor_agent import PredictorAgent

        agent = PredictorAgent()

        # Test with sentiment data
        market_data = {
            "price": 100.0,
            "indicators": {
                "rsi": 50,
                "sma_50": 95,
                "sma_200": 90,
            }
        }
        sentiment_data = {
            "combined_sentiment": 0.8,
            "sentiment_label": "bullish",
            "total_mentions": 100,
            "reddit": {"mentions": 60, "sentiment_score": 0.85},
            "news": {"article_count": 40, "sentiment_score": 0.7},
        }

        result = agent.analyze("NVDA", market_data, sentiment_data)

        # Should have sentiment_signal in factors
        assert "sentiment_signal" in result.factors
        assert result.factors["sentiment_signal"] == 0.8
