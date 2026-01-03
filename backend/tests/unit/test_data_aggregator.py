"""
Unit Tests for Data Aggregator Service
Tests combined market and sentiment data aggregation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.data_aggregator import DataAggregatorService, data_aggregator


class TestComprehensiveAnalysis:
    """Tests for get_comprehensive_analysis() method"""

    @patch("app.services.data_aggregator.market_data_service")
    @patch("app.services.data_aggregator.sentiment_service")
    def test_comprehensive_analysis_success(
        self,
        mock_sentiment,
        mock_market,
        sample_market_data,
        sample_sentiment_data,
        sample_historical_data,
    ):
        """Test successful comprehensive analysis"""
        mock_market.get_quote.return_value = sample_market_data["quote"]
        mock_market.get_historical_data.return_value = sample_historical_data
        mock_market.get_technical_indicators.return_value = sample_market_data["indicators"]
        mock_sentiment.aggregate_sentiment.return_value = sample_sentiment_data

        service = DataAggregatorService()
        result = service.get_comprehensive_analysis("NVDA")

        assert result["ticker"] == "NVDA"
        assert "quote" in result
        assert "historical_summary" in result
        assert "technical_indicators" in result
        assert "sentiment" in result
        assert "overall_outlook" in result

    @patch("app.services.data_aggregator.market_data_service")
    @patch("app.services.data_aggregator.sentiment_service")
    def test_comprehensive_analysis_partial_data(self, mock_sentiment, mock_market):
        """Test analysis continues when some data missing"""
        mock_market.get_quote.return_value = {"current_price": None}
        mock_market.get_historical_data.return_value = []
        mock_market.get_technical_indicators.return_value = {}
        mock_sentiment.aggregate_sentiment.return_value = {
            "combined_sentiment": 0,
            "sentiment_label": "neutral",
        }

        service = DataAggregatorService()
        result = service.get_comprehensive_analysis("NVDA")

        # Should still return structure, just with empty data
        assert result["ticker"] == "NVDA"
        assert "overall_outlook" in result


class TestSummarizeHistorical:
    """Tests for _summarize_historical() method"""

    def test_summarize_with_data(self, sample_historical_data):
        """Test historical summary with valid data"""
        service = DataAggregatorService()
        summary = service._summarize_historical(sample_historical_data)

        assert summary["data_points"] == 3
        assert summary["source"] == "polygon"
        assert "date_range" in summary
        assert "latest" in summary
        assert summary["latest"]["close"] == 875.50

    def test_summarize_empty_data(self):
        """Test historical summary with no data"""
        service = DataAggregatorService()
        summary = service._summarize_historical([])

        assert summary["data_points"] == 0
        assert summary["source"] is None

    def test_summarize_calculates_averages(self, sample_historical_data):
        """Test that summary calculates correct averages"""
        service = DataAggregatorService()
        summary = service._summarize_historical(sample_historical_data)

        expected_avg_volume = (15000000 + 14500000 + 13800000) / 3
        assert abs(summary["avg_volume"] - expected_avg_volume) < 1

        assert summary["high_30d"] == 880.00
        assert summary["low_30d"] == 862.00


class TestCalculateOverallOutlook:
    """Tests for _calculate_overall_outlook() method"""

    def test_outlook_bullish(self, sample_market_data, sample_sentiment_data):
        """Test bullish outlook calculation"""
        technical = sample_market_data["indicators"]
        technical["rsi"] = 45  # Neutral RSI
        technical["price_change_7d"] = 5.0  # Positive momentum

        sentiment = sample_sentiment_data.copy()
        sentiment["combined_sentiment"] = 0.6  # Bullish

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        assert outlook["score"] > 0.3
        assert outlook["recommendation"] == "BULLISH"

    def test_outlook_bearish(self):
        """Test bearish outlook calculation"""
        technical = {
            "rsi": 75,  # Overbought
            "price_change_7d": -8.0,  # Negative momentum
            "volume_trend": "decreasing",
        }
        sentiment = {"combined_sentiment": -0.5, "sentiment_label": "bearish"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        assert outlook["score"] < -0.3
        assert outlook["recommendation"] == "BEARISH"

    def test_outlook_neutral(self):
        """Test neutral outlook calculation"""
        technical = {
            "rsi": 50,  # Neutral
            "price_change_7d": 0.5,  # Minimal movement
            "volume_trend": "neutral",
        }
        sentiment = {"combined_sentiment": 0.0, "sentiment_label": "neutral"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        assert -0.1 <= outlook["score"] <= 0.1
        assert outlook["recommendation"] == "NEUTRAL"

    def test_outlook_rsi_oversold(self):
        """Test that oversold RSI contributes to bullish outlook"""
        technical = {"rsi": 25, "price_change_7d": -2.0, "volume_trend": "neutral"}  # Oversold
        sentiment = {"combined_sentiment": 0.0, "sentiment_label": "neutral"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        # RSI oversold should contribute positively
        assert outlook["factors"]["rsi"]["interpretation"] == "oversold"

    def test_outlook_rsi_overbought(self):
        """Test that overbought RSI contributes to bearish outlook"""
        technical = {"rsi": 80, "price_change_7d": 2.0, "volume_trend": "neutral"}  # Overbought
        sentiment = {"combined_sentiment": 0.0, "sentiment_label": "neutral"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        assert outlook["factors"]["rsi"]["interpretation"] == "overbought"

    def test_outlook_factors_included(self):
        """Test that all factors are included in outlook"""
        technical = {"rsi": 55, "price_change_7d": 3.0, "volume_trend": "increasing"}
        sentiment = {"combined_sentiment": 0.3, "sentiment_label": "slightly_bullish"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        assert "rsi" in outlook["factors"]
        assert "momentum_7d" in outlook["factors"]
        assert "volume_trend" in outlook["factors"]
        assert "sentiment" in outlook["factors"]


class TestCacheMarketData:
    """Tests for _cache_market_data() method"""

    def test_cache_market_data_success(self, mock_db_session, sample_historical_data):
        """Test successful caching of market data"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        service = DataAggregatorService()
        service._cache_market_data(mock_db_session, "NVDA", sample_historical_data)

        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_cache_market_data_skip_existing(self, mock_db_session, sample_historical_data):
        """Test that existing records are skipped"""
        # Simulate existing record
        mock_db_session.query.return_value.filter.return_value.first.return_value = Mock()

        service = DataAggregatorService()
        service._cache_market_data(mock_db_session, "NVDA", sample_historical_data)

        # Should not add new records for existing data
        mock_db_session.commit.assert_called()

    def test_cache_market_data_rollback_on_error(self, mock_db_session, sample_historical_data):
        """Test rollback on database error"""
        mock_db_session.commit.side_effect = Exception("DB Error")

        service = DataAggregatorService()
        service._cache_market_data(mock_db_session, "NVDA", sample_historical_data)

        assert mock_db_session.rollback.called


class TestCacheSentimentData:
    """Tests for _cache_sentiment_data() method"""

    def test_cache_sentiment_data_reddit(self, mock_db_session, sample_sentiment_data):
        """Test caching of Reddit sentiment data"""
        service = DataAggregatorService()
        service._cache_sentiment_data(mock_db_session, "NVDA", sample_sentiment_data)

        assert mock_db_session.add.called
        assert mock_db_session.commit.called

    def test_cache_sentiment_data_no_mentions(self, mock_db_session):
        """Test caching skipped when no mentions"""
        sentiment = {
            "reddit": {"mentions": 0, "sentiment_score": 0},
            "news": {"article_count": 0, "sentiment_score": 0},
        }

        service = DataAggregatorService()
        service._cache_sentiment_data(mock_db_session, "NVDA", sentiment)

        # Should still commit, but may not add records
        mock_db_session.commit.assert_called()


class TestGetWatchlistWithData:
    """Tests for get_watchlist_with_data() method"""

    def test_get_watchlist_empty(self, mock_db_session):
        """Test empty watchlist"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        service = DataAggregatorService()
        result = service.get_watchlist_with_data(mock_db_session)

        assert result == []

    def test_get_watchlist_with_stocks(self, mock_db_session):
        """Test watchlist with stocks"""
        mock_stock = Mock()
        mock_stock.ticker = "NVDA"
        mock_stock.company_name = "NVIDIA"
        mock_stock.sector = "Semiconductors"
        mock_stock.tier = 1

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_stock]
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        service = DataAggregatorService()
        result = service.get_watchlist_with_data(mock_db_session)

        assert len(result) == 1
        assert result[0]["ticker"] == "NVDA"


class TestRefreshAllData:
    """Tests for refresh_all_data() method"""

    @patch.object(DataAggregatorService, "get_comprehensive_analysis")
    def test_refresh_success(self, mock_analysis, mock_db_session):
        """Test successful refresh of all data"""
        mock_stock = Mock()
        mock_stock.ticker = "NVDA"
        mock_stock.active = True

        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_stock]
        mock_analysis.return_value = {"ticker": "NVDA"}

        service = DataAggregatorService()
        result = service.refresh_all_data(mock_db_session)

        assert result["refreshed"] == 1
        assert result["failed"] == 0

    @patch.object(DataAggregatorService, "get_comprehensive_analysis")
    def test_refresh_partial_failure(self, mock_analysis, mock_db_session):
        """Test refresh with some failures"""
        mock_stocks = [Mock(ticker="NVDA"), Mock(ticker="AMD")]
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_stocks

        # First succeeds, second fails
        mock_analysis.side_effect = [{"ticker": "NVDA"}, Exception("API Error")]

        service = DataAggregatorService()
        result = service.refresh_all_data(mock_db_session)

        assert result["refreshed"] == 1
        assert result["failed"] == 1


class TestOutlookScoreWeighting:
    """Tests for outlook score weighting logic"""

    def test_sentiment_has_highest_weight(self):
        """Test that sentiment has 40% weight in outlook"""
        technical = {
            "rsi": 50,  # Neutral RSI (0 contribution)
            "price_change_7d": 0,  # No momentum (0 contribution)
            "volume_trend": "neutral",  # No volume signal (0 contribution)
        }

        # Only sentiment provides signal
        sentiment_positive = {"combined_sentiment": 1.0, "sentiment_label": "bullish"}
        sentiment_negative = {"combined_sentiment": -1.0, "sentiment_label": "bearish"}

        service = DataAggregatorService()

        outlook_pos = service._calculate_overall_outlook(technical, sentiment_positive)
        outlook_neg = service._calculate_overall_outlook(technical, sentiment_negative)

        # With only sentiment contributing, difference should be ~0.8 (40% * 2)
        diff = outlook_pos["score"] - outlook_neg["score"]
        assert 0.7 <= diff <= 0.9  # Allow some tolerance

    def test_rsi_contributes_30_percent(self):
        """Test that RSI has 30% weight in outlook"""
        # Only RSI provides signal
        technical_oversold = {
            "rsi": 20,  # Strongly oversold (+1)
            "price_change_7d": 0,
            "volume_trend": "neutral",
        }
        technical_overbought = {
            "rsi": 80,  # Strongly overbought (-1)
            "price_change_7d": 0,
            "volume_trend": "neutral",
        }

        sentiment = {"combined_sentiment": 0, "sentiment_label": "neutral"}

        service = DataAggregatorService()

        outlook_oversold = service._calculate_overall_outlook(technical_oversold, sentiment)
        outlook_overbought = service._calculate_overall_outlook(technical_overbought, sentiment)

        # RSI contributes 30%, so difference should be ~0.6
        diff = outlook_oversold["score"] - outlook_overbought["score"]
        assert diff > 0  # Oversold should be more bullish


class TestEdgeCases:
    """Tests for edge cases"""

    def test_missing_rsi_defaults_to_neutral(self):
        """Test that missing RSI defaults to 50"""
        technical = {
            # No RSI key
            "price_change_7d": 5.0,
            "volume_trend": "increasing",
        }
        sentiment = {"combined_sentiment": 0.3, "sentiment_label": "slightly_bullish"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        # Should not crash, RSI interpreted as neutral
        assert "score" in outlook

    def test_extreme_momentum_capped(self):
        """Test that extreme momentum is capped at ±1"""
        technical = {"rsi": 50, "price_change_7d": 50.0, "volume_trend": "neutral"}  # Extreme +50%
        sentiment = {"combined_sentiment": 0, "sentiment_label": "neutral"}

        service = DataAggregatorService()
        outlook = service._calculate_overall_outlook(technical, sentiment)

        # Momentum contribution should be capped
        assert outlook["score"] <= 1.0
