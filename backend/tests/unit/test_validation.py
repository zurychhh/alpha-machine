"""
Unit Tests for Input Validation
Tests ticker validation, sanitization, and Pydantic models
"""

import pytest
from pydantic import ValidationError
from app.core.validation import (
    validate_ticker,
    validate_tickers,
    sanitize_text_input,
    sanitize_numeric_input,
    TickerInput,
    TickerListInput,
    AnalysisRequest,
    WatchlistItem,
    PortfolioPositionInput,
    DateRangeInput,
)


class TestValidateTicker:
    """Tests for validate_ticker function"""

    def test_valid_ticker(self):
        """Test valid ticker symbols"""
        assert validate_ticker("NVDA") == "NVDA"
        assert validate_ticker("AAPL") == "AAPL"
        assert validate_ticker("AMD") == "AMD"
        assert validate_ticker("T") == "T"

    def test_lowercase_ticker(self):
        """Test lowercase conversion"""
        assert validate_ticker("nvda") == "NVDA"
        assert validate_ticker("aapl") == "AAPL"

    def test_ticker_with_dollar_sign(self):
        """Test $ prefix removal"""
        assert validate_ticker("$NVDA") == "NVDA"
        assert validate_ticker("$aapl") == "AAPL"

    def test_ticker_with_whitespace(self):
        """Test whitespace handling"""
        assert validate_ticker("  NVDA  ") == "NVDA"
        assert validate_ticker("\tAAPL\n") == "AAPL"

    def test_invalid_ticker_too_long(self):
        """Test rejection of too long tickers"""
        assert validate_ticker("NVDAAA") is None
        assert validate_ticker("APPLESTOCK") is None

    def test_invalid_ticker_has_numbers(self):
        """Test rejection of tickers with numbers"""
        assert validate_ticker("NVD1") is None
        assert validate_ticker("123") is None

    def test_invalid_ticker_special_chars(self):
        """Test rejection of special characters"""
        assert validate_ticker("NV-DA") is None
        assert validate_ticker("NV.DA") is None
        assert validate_ticker("NV/DA") is None

    def test_common_words_excluded(self):
        """Test common words are excluded"""
        assert validate_ticker("THE") is None
        assert validate_ticker("AND") is None
        assert validate_ticker("CEO") is None
        assert validate_ticker("IPO") is None

    def test_empty_ticker(self):
        """Test empty ticker handling"""
        assert validate_ticker("") is None
        assert validate_ticker(None) is None
        assert validate_ticker("   ") is None


class TestValidateTickers:
    """Tests for validate_tickers function"""

    def test_valid_tickers_list(self):
        """Test valid ticker list"""
        result = validate_tickers(["NVDA", "AAPL", "AMD"])
        assert result == ["NVDA", "AAPL", "AMD"]

    def test_mixed_valid_invalid(self):
        """Test mixed valid/invalid tickers"""
        result = validate_tickers(["NVDA", "THE", "AMD", "IPO"])
        assert result == ["NVDA", "AMD"]

    def test_removes_duplicates(self):
        """Test duplicate removal"""
        result = validate_tickers(["NVDA", "nvda", "NVDA", "AAPL"])
        assert result == ["NVDA", "AAPL"]

    def test_empty_after_validation(self):
        """Test empty result when all invalid"""
        result = validate_tickers(["THE", "AND", "CEO"])
        assert result == []


class TestTickerInput:
    """Tests for TickerInput Pydantic model"""

    def test_valid_ticker_input(self):
        """Test valid ticker input"""
        model = TickerInput(ticker="NVDA")
        assert model.ticker == "NVDA"

    def test_lowercase_normalized(self):
        """Test lowercase to uppercase conversion"""
        model = TickerInput(ticker="nvda")
        assert model.ticker == "NVDA"

    def test_invalid_ticker_raises(self):
        """Test invalid ticker raises ValidationError"""
        with pytest.raises(ValidationError):
            TickerInput(ticker="INVALID123")

    def test_excluded_word_raises(self):
        """Test excluded word raises ValidationError"""
        with pytest.raises(ValidationError):
            TickerInput(ticker="CEO")


class TestTickerListInput:
    """Tests for TickerListInput Pydantic model"""

    def test_valid_ticker_list(self):
        """Test valid ticker list"""
        model = TickerListInput(tickers=["NVDA", "AAPL"])
        assert model.tickers == ["NVDA", "AAPL"]

    def test_empty_list_raises(self):
        """Test empty list raises ValidationError"""
        with pytest.raises(ValidationError):
            TickerListInput(tickers=[])

    def test_all_invalid_raises(self):
        """Test all invalid tickers raises ValidationError"""
        with pytest.raises(ValidationError):
            TickerListInput(tickers=["THE", "AND"])


class TestAnalysisRequest:
    """Tests for AnalysisRequest Pydantic model"""

    def test_valid_request(self):
        """Test valid analysis request"""
        model = AnalysisRequest(ticker="NVDA")
        assert model.ticker == "NVDA"
        assert model.include_sentiment is True
        assert model.include_technical is True
        assert model.days_history == 30

    def test_custom_options(self):
        """Test custom analysis options"""
        model = AnalysisRequest(ticker="NVDA", include_sentiment=False, days_history=60)
        assert model.include_sentiment is False
        assert model.days_history == 60

    def test_invalid_days_range(self):
        """Test days_history validation"""
        with pytest.raises(ValidationError):
            AnalysisRequest(ticker="NVDA", days_history=0)

        with pytest.raises(ValidationError):
            AnalysisRequest(ticker="NVDA", days_history=500)


class TestWatchlistItem:
    """Tests for WatchlistItem Pydantic model"""

    def test_valid_watchlist_item(self):
        """Test valid watchlist item"""
        model = WatchlistItem(
            ticker="NVDA", company_name="NVIDIA Corporation", sector="Semiconductors", tier=1
        )
        assert model.ticker == "NVDA"
        assert model.tier == 1

    def test_text_sanitization(self):
        """Test text fields are sanitized"""
        model = WatchlistItem(ticker="NVDA", company_name="<script>alert('xss')</script>NVIDIA")
        assert "<script>" not in model.company_name
        assert "'" not in model.company_name

    def test_tier_validation(self):
        """Test tier range validation"""
        with pytest.raises(ValidationError):
            WatchlistItem(ticker="NVDA", tier=0)

        with pytest.raises(ValidationError):
            WatchlistItem(ticker="NVDA", tier=6)


class TestPortfolioPositionInput:
    """Tests for PortfolioPositionInput Pydantic model"""

    def test_valid_position(self):
        """Test valid portfolio position"""
        model = PortfolioPositionInput(ticker="NVDA", shares=10, entry_price=100.0)
        assert model.ticker == "NVDA"
        assert model.shares == 10
        assert model.entry_price == 100.0

    def test_with_stop_loss_and_target(self):
        """Test position with stop loss and take profit"""
        model = PortfolioPositionInput(
            ticker="NVDA", shares=10, entry_price=100.0, stop_loss=90.0, take_profit=120.0
        )
        assert model.stop_loss == 90.0
        assert model.take_profit == 120.0

    def test_invalid_stop_loss(self):
        """Test stop loss must be below entry"""
        with pytest.raises(ValidationError):
            PortfolioPositionInput(
                ticker="NVDA", shares=10, entry_price=100.0, stop_loss=110.0  # Above entry
            )

    def test_invalid_take_profit(self):
        """Test take profit must be above entry"""
        with pytest.raises(ValidationError):
            PortfolioPositionInput(
                ticker="NVDA", shares=10, entry_price=100.0, take_profit=90.0  # Below entry
            )

    def test_zero_shares_invalid(self):
        """Test shares must be positive"""
        with pytest.raises(ValidationError):
            PortfolioPositionInput(ticker="NVDA", shares=0, entry_price=100.0)


class TestDateRangeInput:
    """Tests for DateRangeInput Pydantic model"""

    def test_valid_date_range(self):
        """Test valid date range"""
        model = DateRangeInput(start_date="2024-01-01", end_date="2024-12-31")
        assert model.start_date == "2024-01-01"
        assert model.end_date == "2024-12-31"

    def test_invalid_date_format(self):
        """Test invalid date format rejected"""
        with pytest.raises(ValidationError):
            DateRangeInput(start_date="01-01-2024")

    def test_invalid_date_order(self):
        """Test end_date before start_date rejected"""
        with pytest.raises(ValidationError):
            DateRangeInput(start_date="2024-12-31", end_date="2024-01-01")


class TestSanitizeTextInput:
    """Tests for sanitize_text_input function"""

    def test_sanitize_normal_text(self):
        """Test normal text unchanged"""
        assert sanitize_text_input("Hello World") == "Hello World"

    def test_remove_html_tags(self):
        """Test HTML tag removal"""
        result = sanitize_text_input("<script>alert('xss')</script>Hello")
        assert "<" not in result
        assert ">" not in result

    def test_remove_quotes(self):
        """Test quote removal"""
        result = sanitize_text_input("Hello \"World\" and 'Foo'")
        assert '"' not in result
        assert "'" not in result

    def test_truncate_long_text(self):
        """Test text truncation"""
        long_text = "A" * 2000
        result = sanitize_text_input(long_text, max_length=100)
        assert len(result) == 100

    def test_none_returns_none(self):
        """Test None input returns None"""
        assert sanitize_text_input(None) is None

    def test_empty_after_sanitize(self):
        """Test empty string returns None"""
        assert sanitize_text_input("   ") is None


class TestSanitizeNumericInput:
    """Tests for sanitize_numeric_input function"""

    def test_valid_number(self):
        """Test valid number unchanged"""
        assert sanitize_numeric_input(50.0) == 50.0

    def test_clamp_to_min(self):
        """Test clamping to minimum"""
        result = sanitize_numeric_input(-10.0, min_val=0.0)
        assert result == 0.0

    def test_clamp_to_max(self):
        """Test clamping to maximum"""
        result = sanitize_numeric_input(200.0, max_val=100.0)
        assert result == 100.0

    def test_default_on_none(self):
        """Test default value on None input"""
        result = sanitize_numeric_input(None, default=30.0)
        assert result == 30.0

    def test_none_returns_none(self):
        """Test None with no default returns None"""
        assert sanitize_numeric_input(None) is None
