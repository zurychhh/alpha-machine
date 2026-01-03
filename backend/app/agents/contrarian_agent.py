"""
Contrarian Agent - Deep Value / Contrarian Analysis
Uses OpenAI GPT-4o for contrarian investment perspective.
Buys when others are fearful, sells when others are greedy.
"""

import os
import json
from typing import Dict, Optional, List
from openai import OpenAI
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.core.retry import with_retry, CircuitBreaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ContrarianAgent(BaseAgent):
    """
    Contrarian analyst agent powered by OpenAI GPT-4o.

    This agent focuses on contrarian indicators:
    - Fear and greed extremes (buy fear, sell greed)
    - Oversold/overbought conditions
    - Sentiment divergences
    - Value in fear, danger in euphoria
    """

    SYSTEM_PROMPT = """You are a contrarian value investor who profits by going against the crowd.

Your core philosophy:
1. Buy when others are fearful (negative sentiment + oversold RSI < 30)
2. Sell when others are greedy (extreme positive sentiment + overbought RSI > 70)
3. Look for value in fear, recognize danger in euphoria
4. The crowd is usually wrong at extremes

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
    "signal": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": 0.0 to 1.0,
    "score": -1.0 to 1.0,
    "reasoning": "Your contrarian analysis in 2-3 sentences",
    "factors": {
        "fear_greed_signal": -1.0 to 1.0,
        "oversold_overbought": -1.0 to 1.0,
        "sentiment_divergence": -1.0 to 1.0,
        "crowd_position": -1.0 to 1.0
    }
}

Score interpretation:
- score > 0.6: STRONG_BUY (extreme fear = buying opportunity)
- score 0.2 to 0.6: BUY (fearful sentiment, potential value)
- score -0.2 to 0.2: HOLD (no extreme to exploit)
- score -0.6 to -0.2: SELL (greed building)
- score < -0.6: STRONG_SELL (extreme greed = selling opportunity)

Be contrarian - when everyone is bullish, be cautious. When everyone is bearish, look for value."""

    def __init__(
        self,
        name: str = "ContrarianAgent",
        weight: float = 1.0,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the contrarian agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
            model: OpenAI model to use
            api_key: OpenAI API key (defaults to env var)
        """
        super().__init__(name=name, weight=weight)
        self.model_name = model
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, name="openai_api"
        )

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Perform contrarian analysis using GPT-4o.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data (price, volume, indicators)
            sentiment_data: Sentiment analysis data
            historical_data: Historical price data

        Returns:
            AgentSignal with contrarian recommendation
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

            # Call OpenAI API with retry
            response = self._call_openai(prompt)

            # Parse and validate response
            return self._parse_response(ticker, response)

        except Exception as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Contrarian analysis failed for {ticker}: {e}")
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
            f"Analyze {ticker} from a CONTRARIAN perspective.",
            "",
            "=== CURRENT DATA ===",
            f"Ticker: {ticker}",
            f"Current Price: ${current_price}",
        ]

        # Add technical indicators
        if indicators:
            prompt_parts.append("\n=== TECHNICAL INDICATORS ===")
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                prompt_parts.append(f"RSI: {rsi:.1f}")
                if rsi < 30:
                    prompt_parts.append("  -> OVERSOLD (contrarian bullish signal)")
                elif rsi > 70:
                    prompt_parts.append("  -> OVERBOUGHT (contrarian bearish signal)")
            if "price_change_7d" in indicators:
                prompt_parts.append(
                    f"7-Day Change: {indicators['price_change_7d']:+.2f}%"
                )
            if "price_change_30d" in indicators:
                prompt_parts.append(
                    f"30-Day Change: {indicators['price_change_30d']:+.2f}%"
                )

        # Add sentiment data - key for contrarian analysis
        if sentiment_data:
            prompt_parts.append("\n=== SENTIMENT (Crowd Mood) ===")
            if "combined_sentiment" in sentiment_data:
                sentiment = sentiment_data["combined_sentiment"]
                prompt_parts.append(f"Combined Sentiment: {sentiment:.3f}")
                if sentiment > 0.5:
                    prompt_parts.append("  -> EXTREME GREED (contrarian sell signal)")
                elif sentiment < -0.5:
                    prompt_parts.append("  -> EXTREME FEAR (contrarian buy signal)")
            if "sentiment_label" in sentiment_data:
                prompt_parts.append(f"Sentiment Label: {sentiment_data['sentiment_label']}")
            if "total_mentions" in sentiment_data:
                prompt_parts.append(f"Total Mentions: {sentiment_data['total_mentions']}")

        # Add historical context
        if historical_data and len(historical_data) > 0:
            prompt_parts.append("\n=== HISTORICAL CONTEXT ===")
            prompt_parts.append(f"Data points: {len(historical_data)} days")

        prompt_parts.extend([
            "",
            "=== YOUR CONTRARIAN TASK ===",
            "Evaluate this stock from a contrarian perspective:",
            "1. Is the crowd overly fearful? (opportunity to buy)",
            "2. Is the crowd overly greedy? (time to sell)",
            "3. Are there extreme technical conditions (oversold/overbought)?",
            "4. Does sentiment diverge from fundamentals?",
            "",
            "Remember: Contrarians profit by doing the opposite of the emotional crowd.",
            "",
            "Respond with ONLY the JSON object as specified."
        ])

        return "\n".join(prompt_parts)

    @with_retry(max_retries=2, initial_delay=1.0, backoff_factor=2.0)
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API with retry logic."""
        self.logger.debug(f"Calling OpenAI API with model {self.model_name}")

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        self._circuit_breaker.record_success()

        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content

        raise ValueError("Empty response from OpenAI API")

    def _parse_response(self, ticker: str, response: str) -> AgentSignal:
        """Parse OpenAI's JSON response into an AgentSignal."""
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
                reasoning=f"[Contrarian] {reasoning}",
                factors=factors,
                raw_score=score,
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse OpenAI response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}")
            return self.create_neutral_signal(ticker, "Failed to parse AI response")
        except Exception as e:
            self.logger.error(f"Error processing OpenAI response: {e}")
            return self.create_neutral_signal(ticker, "Response processing error")
