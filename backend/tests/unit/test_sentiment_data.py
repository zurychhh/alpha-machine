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
        """Test sentiment analysis of positive Reddit post"""
        mock_reddit_submission.title = "NVDA to the moon! Bullish calls, strong buy!"

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        assert sentiment == 1  # Positive

    def test_analyze_reddit_post_negative(self, mock_reddit_submission):
        """Test sentiment analysis of negative Reddit post"""
        mock_reddit_submission.title = "NVDA crash incoming, bearish puts, sell now!"
        mock_reddit_submission.score = -10  # Negative score
        mock_reddit_submission.upvote_ratio = 0.3

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        assert sentiment == -1  # Negative

    def test_analyze_reddit_post_neutral(self, mock_reddit_submission):
        """Test sentiment analysis of neutral Reddit post"""
        mock_reddit_submission.title = "What do you think about NVDA?"
        mock_reddit_submission.score = 25
        mock_reddit_submission.upvote_ratio = 0.5

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        assert sentiment == 0  # Neutral

    def test_analyze_reddit_post_high_score_bonus(self, mock_reddit_submission):
        """Test that high score + upvote ratio adds positive sentiment"""
        mock_reddit_submission.title = "NVDA discussion"  # Neutral title
        mock_reddit_submission.score = 500
        mock_reddit_submission.upvote_ratio = 0.95

        service = SentimentDataService()
        sentiment = service._analyze_reddit_post(mock_reddit_submission)

        assert sentiment == 1  # Positive due to high engagement


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
    """Tests for _analyze_headline() method"""

    def test_positive_headline(self):
        """Test positive headline detection"""
        service = SentimentDataService()

        headlines = [
            "NVDA stock surges on strong earnings",
            "NVIDIA rally continues as AI demand soars",
            "Analysts upgrade NVDA with bullish outlook",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            assert sentiment == 1, f"Expected positive for: {headline}"

    def test_negative_headline(self):
        """Test negative headline detection"""
        service = SentimentDataService()

        headlines = [
            "NVDA plunges on weak guidance",
            "NVIDIA stock crashes amid market selloff",
            "Concerns grow over NVDA valuation",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            assert sentiment == -1, f"Expected negative for: {headline}"

    def test_neutral_headline(self):
        """Test neutral headline detection"""
        service = SentimentDataService()

        headlines = [
            "NVDA reports quarterly results",
            "NVIDIA announces new product",
            "Tech stocks mixed in trading",
        ]

        for headline in headlines:
            sentiment = service._analyze_headline(headline)
            assert sentiment == 0, f"Expected neutral for: {headline}"


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
        result = service.aggregate_sentiment("NVDA")

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
        result = service.aggregate_sentiment("NVDA")

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
        result = service.aggregate_sentiment("NVDA")

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
        result = service.aggregate_sentiment("NVDA")

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
        result = service.aggregate_sentiment("NVDA")

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
        assert sentiment == 0
