"""
Unit Tests for Market Data Service
Tests all market data methods with mocked API responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import responses
from app.services.market_data import MarketDataService, market_data_service


class TestGetCurrentPrice:
    """Tests for get_current_price() method"""

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_polygon_success(self, mock_get, mock_settings, mock_polygon_success_response):
        """Test successful price fetch from Polygon.io"""
        mock_settings.POLYGON_API_KEY = "test_key"
        mock_settings.FINNHUB_API_KEY = None
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_polygon_success_response)

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price == 875.50
        mock_get.assert_called_once()

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_polygon_fails_finnhub_succeeds(
        self, mock_get, mock_settings, mock_finnhub_success_response
    ):
        """Test fallback to Finnhub when Polygon fails"""
        mock_settings.POLYGON_API_KEY = "test_key"
        mock_settings.FINNHUB_API_KEY = "test_key"

        # Use 404 (non-retryable) to simulate Polygon fail, then Finnhub success
        mock_get.side_effect = [
            Mock(status_code=404),  # Polygon fails (non-retryable)
            Mock(status_code=200, json=lambda: mock_finnhub_success_response),  # Finnhub succeeds
        ]

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price == 875.50
        assert mock_get.call_count == 2

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_all_sources_fail(self, mock_get, mock_settings):
        """Test graceful failure when all sources fail"""
        mock_settings.POLYGON_API_KEY = "test_key"
        mock_settings.FINNHUB_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=500)

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price is None

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_no_api_keys_configured(self, mock_get, mock_settings):
        """Test behavior when no API keys are configured"""
        mock_settings.POLYGON_API_KEY = None
        mock_settings.FINNHUB_API_KEY = None

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price is None
        mock_get.assert_not_called()

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_api_timeout(self, mock_get, mock_settings):
        """Test handling of API timeout"""
        import requests

        mock_settings.POLYGON_API_KEY = "test_key"
        mock_settings.FINNHUB_API_KEY = None

        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price is None

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_malformed_response(self, mock_get, mock_settings):
        """Test handling of malformed API response"""
        mock_settings.POLYGON_API_KEY = "test_key"
        mock_settings.FINNHUB_API_KEY = None

        # Response without expected 'results' key
        mock_get.return_value = Mock(
            status_code=200, json=lambda: {"status": "OK"}  # Missing 'results'
        )

        service = MarketDataService()
        price = service.get_current_price("NVDA")

        assert price is None


class TestGetHistoricalData:
    """Tests for get_historical_data() method"""

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_alphavantage_success(self, mock_get, mock_settings, mock_alphavantage_daily_response):
        """Test successful historical data from Alpha Vantage"""
        mock_settings.ALPHA_VANTAGE_API_KEY = "test_key"
        mock_settings.POLYGON_API_KEY = None

        mock_get.return_value = Mock(status_code=200, json=lambda: mock_alphavantage_daily_response)

        service = MarketDataService()
        data = service.get_historical_data("NVDA", days=3)

        assert len(data) == 3
        assert data[0]["close"] == 875.50
        assert data[0]["source"] == "alphavantage"

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_alphavantage_rate_limit(
        self, mock_get, mock_settings, mock_alphavantage_rate_limit_response
    ):
        """Test handling of Alpha Vantage rate limit"""
        mock_settings.ALPHA_VANTAGE_API_KEY = "test_key"
        mock_settings.POLYGON_API_KEY = None

        mock_get.return_value = Mock(
            status_code=200, json=lambda: mock_alphavantage_rate_limit_response
        )

        service = MarketDataService()
        data = service.get_historical_data("NVDA", days=30)

        assert data == []

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_polygon_fallback(self, mock_get, mock_settings, mock_polygon_historical_response):
        """Test fallback to Polygon when Alpha Vantage fails"""
        mock_settings.ALPHA_VANTAGE_API_KEY = "test_key"
        mock_settings.POLYGON_API_KEY = "test_key"

        # Use 401 (non-retryable) to simulate Alpha Vantage fail, then Polygon success
        mock_get.side_effect = [
            Mock(status_code=401),  # Alpha Vantage fails (non-retryable)
            Mock(status_code=200, json=lambda: mock_polygon_historical_response),
        ]

        service = MarketDataService()
        data = service.get_historical_data("NVDA", days=3)

        assert len(data) > 0
        assert mock_get.call_count == 2

    @patch("app.services.market_data.settings")
    def test_no_api_keys(self, mock_settings):
        """Test behavior when no API keys configured"""
        mock_settings.ALPHA_VANTAGE_API_KEY = None
        mock_settings.POLYGON_API_KEY = None

        service = MarketDataService()
        data = service.get_historical_data("NVDA", days=30)

        assert data == []


class TestGetTechnicalIndicators:
    """Tests for get_technical_indicators() method"""

    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_rsi_from_alphavantage(self, mock_get, mock_settings, mock_alphavantage_rsi_response):
        """Test RSI fetch from Alpha Vantage"""
        mock_settings.ALPHA_VANTAGE_API_KEY = "test_key"

        mock_get.return_value = Mock(status_code=200, json=lambda: mock_alphavantage_rsi_response)

        service = MarketDataService()
        indicators = service.get_technical_indicators("NVDA")

        assert "rsi" in indicators
        assert indicators["rsi"] == 55.50

    @patch.object(MarketDataService, "get_historical_data")
    @patch.object(MarketDataService, "_get_rsi_alphavantage")
    def test_rsi_calculation_fallback(self, mock_rsi, mock_historical, sample_historical_data):
        """Test RSI calculation from historical data when API fails"""
        mock_rsi.return_value = None
        mock_historical.return_value = sample_historical_data * 7  # Need 20+ days

        service = MarketDataService()
        indicators = service.get_technical_indicators("NVDA")

        # Should have calculated RSI even without API
        assert "rsi" in indicators


class TestCalculateRSI:
    """Tests for _calculate_rsi() method"""

    def test_calculate_rsi_normal(self):
        """Test RSI calculation with normal data"""
        service = MarketDataService()

        # Create 20 days of data with slight upward trend
        historical = []
        price = 100
        for i in range(20):
            price += 0.5 if i % 2 == 0 else -0.3  # Slight upward bias
            historical.append({"close": price})

        rsi = service._calculate_rsi(historical, period=14)

        assert 0 <= rsi <= 100

    def test_calculate_rsi_all_gains(self):
        """Test RSI when all days are gains (should be ~100)"""
        service = MarketDataService()

        # Data should be newest-first (historical[0] = most recent)
        # When reversed for calculation, we get oldest-first with ascending prices = all gains
        historical = [{"close": 119 - i} for i in range(20)]  # [119, 118, ..., 100]

        rsi = service._calculate_rsi(historical, period=14)

        assert rsi == 100.0

    def test_calculate_rsi_insufficient_data(self):
        """Test RSI with insufficient data returns neutral 50"""
        service = MarketDataService()

        historical = [{"close": 100}, {"close": 101}]  # Only 2 days

        rsi = service._calculate_rsi(historical, period=14)

        assert rsi == 50.0  # Default neutral


class TestCalculatePriceChange:
    """Tests for _calculate_price_change() method"""

    def test_price_change_positive(self):
        """Test positive price change calculation"""
        service = MarketDataService()

        historical = [
            {"close": 110.0},  # Current (index 0)
            {"close": 100.0},  # 1 day ago (index 1)
        ]

        # days=2 compares historical[0] with historical[1]
        change = service._calculate_price_change(historical, days=2)

        assert change == 10.0  # 10% increase

    def test_price_change_negative(self):
        """Test negative price change calculation"""
        service = MarketDataService()

        historical = [
            {"close": 90.0},  # Current (index 0)
            {"close": 100.0},  # 1 day ago (index 1)
        ]

        # days=2 compares historical[0] with historical[1]
        change = service._calculate_price_change(historical, days=2)

        assert change == -10.0  # 10% decrease

    def test_price_change_insufficient_data(self):
        """Test price change with insufficient data"""
        service = MarketDataService()

        historical = [{"close": 100.0}]  # Only 1 day

        change = service._calculate_price_change(historical, days=7)

        assert change == 0.0


class TestCalculateVolumeTrend:
    """Tests for _calculate_volume_trend() method"""

    def test_volume_increasing(self):
        """Test detection of increasing volume"""
        service = MarketDataService()

        # Recent volume higher than older
        historical = [
            {"volume": 1500000},  # Most recent
            {"volume": 1400000},
            {"volume": 1300000},
            {"volume": 1200000},
            {"volume": 1100000},
            {"volume": 800000},  # Older
            {"volume": 750000},
            {"volume": 700000},
            {"volume": 650000},
            {"volume": 600000},
        ]

        trend = service._calculate_volume_trend(historical)

        assert trend == "increasing"

    def test_volume_decreasing(self):
        """Test detection of decreasing volume"""
        service = MarketDataService()

        # Recent volume lower than older
        historical = [
            {"volume": 600000},
            {"volume": 650000},
            {"volume": 700000},
            {"volume": 750000},
            {"volume": 800000},
            {"volume": 1100000},
            {"volume": 1200000},
            {"volume": 1300000},
            {"volume": 1400000},
            {"volume": 1500000},
        ]

        trend = service._calculate_volume_trend(historical)

        assert trend == "decreasing"

    def test_volume_neutral(self):
        """Test detection of neutral volume"""
        service = MarketDataService()

        # Stable volume
        historical = [{"volume": 1000000} for _ in range(10)]

        trend = service._calculate_volume_trend(historical)

        assert trend == "neutral"


class TestGetQuote:
    """Tests for get_quote() method"""

    @patch.object(MarketDataService, "get_current_price")
    @patch("app.services.market_data.settings")
    @patch("requests.get")
    def test_quote_success(
        self, mock_get, mock_settings, mock_price, mock_finnhub_success_response
    ):
        """Test successful quote retrieval"""
        mock_settings.FINNHUB_API_KEY = "test_key"
        mock_price.return_value = 875.50
        mock_get.return_value = Mock(status_code=200, json=lambda: mock_finnhub_success_response)

        service = MarketDataService()
        quote = service.get_quote("NVDA")

        assert quote["ticker"] == "NVDA"
        assert quote["current_price"] == 875.50
        assert quote["high"] == 880.00
        assert quote["low"] == 870.00

    @patch.object(MarketDataService, "get_current_price")
    def test_quote_no_price(self, mock_price):
        """Test quote when price unavailable"""
        mock_price.return_value = None

        service = MarketDataService()
        quote = service.get_quote("INVALID")

        assert quote["current_price"] is None
