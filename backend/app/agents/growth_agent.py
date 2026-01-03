"""
Growth Agent - Momentum and Growth Analysis
Uses Claude Sonnet 4 for growth-focused investment perspective.
Focuses on momentum, trend strength, and risk-adjusted returns.
"""

import os
import json
from typing import Dict, Optional, List
from anthropic import Anthropic
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.core.retry import with_retry, CircuitBreaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class GrowthAgent(BaseAgent):
    """
    Growth analyst agent powered by Claude Sonnet 4.

    This agent focuses on growth characteristics:
    - Momentum and trend strength
    - Risk-adjusted returns
    - Growth potential vs current valuation
    - Technical confirmation of trends
    """

    SYSTEM_PROMPT = """You are a growth-focused stock analyst who identifies momentum and growth opportunities.

Your growth philosophy:
1. Buy strong momentum stocks (>10% monthly gain) with positive sentiment
2. Avoid negative momentum (<-5%) even if cheap
3. Risk management: Never buy overbought (RSI > 75) without confirmation
4. Prefer stocks with increasing volume + positive sentiment

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
    "signal": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": 0.0 to 1.0,
    "score": -1.0 to 1.0,
    "reasoning": "Your growth analysis in 2-3 sentences",
    "factors": {
        "momentum_strength": -1.0 to 1.0,
        "trend_quality": 0.0 to 1.0,
        "growth_potential": 0.0 to 1.0,
        "risk_adjusted_score": -1.0 to 1.0
    }
}

Score interpretation:
- score > 0.6: STRONG_BUY (strong growth momentum)
- score 0.2 to 0.6: BUY (positive growth signals)
- score -0.2 to 0.2: HOLD (unclear growth trajectory)
- score -0.6 to -0.2: SELL (weakening growth)
- score < -0.6: STRONG_SELL (deteriorating growth)

Be data-driven and focus on growth metrics. Momentum is key."""

    def __init__(
        self,
        name: str = "GrowthAgent",
        weight: float = 1.0,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the growth agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
            model: Claude model to use
            api_key: Anthropic API key (defaults to env var)
        """
        super().__init__(name=name, weight=weight)
        self.model_name = model
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self._client = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, name="anthropic_api"
        )

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Perform growth analysis using Claude.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data (price, volume, indicators)
            sentiment_data: Sentiment analysis data
            historical_data: Historical price data

        Returns:
            AgentSignal with growth-focused recommendation
        """
        if not self.validate_inputs(ticker, market_data):
            return self.create_neutral_signal(ticker, "Invalid input data")

        # Check circuit breaker
        if not self._circuit_breaker.can_execute():
            self.logger.warning("Circuit breaker open, returning neutral signal")
            return self.create_neutral_signal(ticker, "API temporarily unavailable")

        try:
            # Build the analysis prompt
            prompt = self._build_prompt(
                ticker, market_data, sentiment_data, historical_data
            )

            # Call Claude API with retry
            response = self._call_claude(prompt)

            # Parse and validate response
            return self._parse_response(ticker, response)

        except Exception as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Growth analysis failed for {ticker}: {e}")
            return self.create_neutral_signal(ticker, f"Analysis error: {str(e)[:100]}")

    def _build_prompt(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict],
        historical_data: Optional[List[Dict]],
    ) -> str:
        """Build the analysis prompt with all available data."""

        # Extract key metrics
        indicators = market_data.get("indicators", market_data)
        current_price = market_data.get(
            "current_price", market_data.get("price", "N/A")
        )

        prompt_parts = [
            f"Analyze {ticker} from a GROWTH and MOMENTUM perspective.",
            "",
            "=== CURRENT DATA ===",
            f"Ticker: {ticker}",
            f"Current Price: ${current_price}",
        ]

        # Add technical indicators
        if indicators:
            prompt_parts.append("\n=== TECHNICAL INDICATORS ===")
            if "rsi" in indicators:
                prompt_parts.append(f"RSI: {indicators['rsi']:.1f}")
            if "price_change_7d" in indicators:
                change_7d = indicators["price_change_7d"]
                prompt_parts.append(f"7-Day Change: {change_7d:+.2f}%")
                if change_7d > 10:
                    prompt_parts.append("  -> STRONG 7-DAY MOMENTUM")
            if "price_change_30d" in indicators:
                change_30d = indicators["price_change_30d"]
                prompt_parts.append(f"30-Day Change: {change_30d:+.2f}%")
                if change_30d > 15:
                    prompt_parts.append("  -> STRONG 30-DAY TREND")
                elif change_30d < -10:
                    prompt_parts.append("  -> NEGATIVE MOMENTUM - CAUTION")
            if "volume_trend" in indicators:
                prompt_parts.append(f"Volume Trend: {indicators['volume_trend']}")
            if "sma_50" in indicators:
                prompt_parts.append(f"50-Day SMA: ${indicators['sma_50']:.2f}")
            if "sma_200" in indicators:
                prompt_parts.append(f"200-Day SMA: ${indicators['sma_200']:.2f}")

        # Add momentum metrics
        if indicators:
            prompt_parts.append("\n=== MOMENTUM METRICS ===")
            # Calculate position relative to moving averages
            if "sma_50" in indicators and current_price != "N/A":
                try:
                    price = float(current_price)
                    sma = float(indicators["sma_50"])
                    pct_from_sma = ((price - sma) / sma) * 100
                    prompt_parts.append(f"Distance from 50-SMA: {pct_from_sma:+.2f}%")
                    if pct_from_sma > 10:
                        prompt_parts.append("  -> Trading well above 50-SMA (bullish)")
                    elif pct_from_sma < -10:
                        prompt_parts.append("  -> Trading below 50-SMA (bearish)")
                except (ValueError, ZeroDivisionError):
                    pass

        # Add sentiment data
        if sentiment_data:
            prompt_parts.append("\n=== SENTIMENT DATA ===")
            if "combined_sentiment" in sentiment_data:
                prompt_parts.append(
                    f"Combined Sentiment: {sentiment_data['combined_sentiment']:.3f}"
                )
            if "sentiment_label" in sentiment_data:
                prompt_parts.append(
                    f"Sentiment Label: {sentiment_data['sentiment_label']}"
                )
            if "total_mentions" in sentiment_data:
                prompt_parts.append(
                    f"Total Mentions: {sentiment_data['total_mentions']}"
                )

        # Add historical trends if available
        if historical_data and len(historical_data) > 0:
            prompt_parts.append("\n=== HISTORICAL TRENDS ===")
            prompt_parts.append(f"Data points: {len(historical_data)} days")

            # Calculate trend metrics
            if len(historical_data) >= 5:
                closes = [d.get("close", 0) for d in historical_data if d.get("close")]
                if len(closes) >= 5:
                    # Check if trending up (higher highs)
                    recent = closes[-5:]
                    trend = "upward" if recent[-1] > recent[0] else "downward"
                    prompt_parts.append(f"Recent 5-day trend: {trend}")

        prompt_parts.extend([
            "",
            "=== YOUR GROWTH TASK ===",
            "Evaluate this stock from a growth/momentum perspective:",
            "1. Is momentum strong and sustainable? (>10% monthly = strong)",
            "2. Does the technical setup support growth continuation?",
            "3. Is sentiment supportive of further gains?",
            "4. What is the growth potential vs risk?",
            "",
            "Remember: Growth investors ride momentum - buy strength, sell weakness.",
            "",
            "Respond with ONLY the JSON object as specified."
        ])

        return "\n".join(prompt_parts)

    @with_retry(max_retries=2, initial_delay=1.0, backoff_factor=2.0)
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with retry logic."""
        self.logger.debug(f"Calling Claude API with model {self.model_name}")

        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": f"{self.SYSTEM_PROMPT}\n\n---\n\n{prompt}"}]
        )

        self._circuit_breaker.record_success()

        if message.content and len(message.content) > 0:
            return message.content[0].text

        raise ValueError("Empty response from Claude API")

    def _parse_response(self, ticker: str, response: str) -> AgentSignal:
        """Parse Claude's JSON response into an AgentSignal."""
        try:
            # Try to extract JSON from response
            response = response.strip()

            # Handle potential markdown code blocks
            if response.startswith("```"):
                lines = response.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```") and not in_json:
                        in_json = True
                        continue
                    elif line.startswith("```") and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                response = "\n".join(json_lines)

            data = json.loads(response)

            # Validate required fields
            signal_str = data.get("signal", "HOLD")
            confidence = float(data.get("confidence", 0.5))
            score = float(data.get("score", 0.0))
            reasoning = data.get("reasoning", "No reasoning provided")
            factors = data.get("factors", {})

            # Map signal string to SignalType
            signal_map = {
                "STRONG_BUY": SignalType.STRONG_BUY,
                "BUY": SignalType.BUY,
                "HOLD": SignalType.HOLD,
                "SELL": SignalType.SELL,
                "STRONG_SELL": SignalType.STRONG_SELL,
            }
            signal = signal_map.get(signal_str.upper(), SignalType.HOLD)

            # Clamp values to valid ranges
            confidence = max(0.0, min(1.0, confidence))
            score = max(-1.0, min(1.0, score))

            return AgentSignal(
                agent_name=self.name,
                ticker=ticker,
                signal=signal,
                confidence=confidence,
                reasoning=f"[Growth] {reasoning}",
                factors=factors,
                raw_score=score,
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse Claude response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}")
            return self.create_neutral_signal(ticker, "Failed to parse AI response")
        except Exception as e:
            self.logger.error(f"Error processing Claude response: {e}")
            return self.create_neutral_signal(ticker, "Response processing error")
