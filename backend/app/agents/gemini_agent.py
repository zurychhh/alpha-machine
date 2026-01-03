"""
Gemini Agent - Growth Analyst
Uses Google Gemini API for growth-focused stock analysis.
Identifies momentum, growth potential, and market leadership.
"""

import os
import json
from typing import Dict, Optional, List
import google.generativeai as genai
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.core.retry import with_retry, CircuitBreaker
import logging

logger = logging.getLogger(__name__)


class GeminiAgent(BaseAgent):
    """
    Growth analyst agent powered by Google Gemini.

    This agent focuses on growth characteristics:
    - Momentum and trend strength
    - Market leadership indicators
    - Growth potential vs current valuation
    - Sector and industry trends
    """

    SYSTEM_PROMPT = """You are a growth-focused stock analyst who identifies momentum and growth opportunities.

Your role is to evaluate stocks based on:
1. Momentum strength - is the trend strong and sustainable?
2. Growth indicators - revenue growth, market expansion potential
3. Market leadership - is this a leader or laggard in its sector?
4. Technical momentum - RSI, moving averages, volume confirmation

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
        "market_leadership": 0.0 to 1.0
    }
}

Score interpretation:
- score > 0.6: STRONG_BUY (strong growth momentum)
- score 0.2 to 0.6: BUY (positive growth signals)
- score -0.2 to 0.2: HOLD (unclear growth trajectory)
- score -0.6 to -0.2: SELL (weakening growth)
- score < -0.6: STRONG_SELL (deteriorating growth)

Be data-driven and focus on growth metrics. Base your analysis on the provided data."""

    def __init__(
        self,
        name: str = "GeminiGrowthAgent",
        weight: float = 1.0,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Gemini growth agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
            model: Gemini model to use
            api_key: Google AI API key (defaults to env var)
        """
        super().__init__(name=name, weight=weight)
        self.model_name = model
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        self._model = None
        self._configured = False
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, name="gemini_api"
        )

    @property
    def model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            if not self.api_key:
                raise ValueError("GOOGLE_AI_API_KEY not set")
            if not self._configured:
                genai.configure(api_key=self.api_key)
                self._configured = True
            self._model = genai.GenerativeModel(self.model_name)
        return self._model

    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Perform growth analysis using Gemini.

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

            # Call Gemini API with retry
            response = self._call_gemini(prompt)

            # Parse and validate response
            return self._parse_response(ticker, response)

        except Exception as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Gemini analysis failed for {ticker}: {e}")
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
            self.SYSTEM_PROMPT,
            "",
            "---",
            "",
            f"Analyze {ticker} from a GROWTH perspective.",
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
                prompt_parts.append(
                    f"7-Day Change: {indicators['price_change_7d']:+.2f}%"
                )
            if "price_change_30d" in indicators:
                prompt_parts.append(
                    f"30-Day Change: {indicators['price_change_30d']:+.2f}%"
                )
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

        prompt_parts.extend(
            [
                "",
                "=== YOUR TASK ===",
                "Provide your growth analysis. Evaluate:",
                "1. Is momentum strong and sustainable?",
                "2. Does the technical setup support growth continuation?",
                "3. Is sentiment supportive of further gains?",
                "4. What is the growth potential vs risk?",
                "",
                "Respond with ONLY the JSON object as specified.",
            ]
        )

        return "\n".join(prompt_parts)

    @with_retry(max_retries=2, initial_delay=1.0, backoff_factor=2.0)
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with retry logic."""
        self.logger.debug(f"Calling Gemini API with model {self.model_name}")

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=500,
                temperature=0.3,
            ),
        )

        self._circuit_breaker.record_success()

        if response.text:
            return response.text

        raise ValueError("Empty response from Gemini API")

    def _parse_response(self, ticker: str, response: str) -> AgentSignal:
        """Parse Gemini's JSON response into an AgentSignal."""
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
            self.logger.warning(f"Failed to parse Gemini response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}")
            return self.create_neutral_signal(ticker, f"Failed to parse AI response")
        except Exception as e:
            self.logger.error(f"Error processing Gemini response: {e}")
            return self.create_neutral_signal(ticker, f"Response processing error")
