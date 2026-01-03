"""
Claude Agent - Contrarian Analyst
Uses Anthropic Claude API for contrarian analysis of stocks.
Challenges conventional wisdom and identifies overlooked risks/opportunities.
"""

import os
import json
from typing import Dict, Optional, List
from anthropic import Anthropic
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.core.retry import with_retry, CircuitBreaker
import logging

logger = logging.getLogger(__name__)


class ClaudeAgent(BaseAgent):
    """
    Contrarian analyst agent powered by Claude.

    This agent takes a contrarian perspective, questioning popular narratives
    and identifying:
    - Overlooked risks in bullish stocks
    - Hidden opportunities in beaten-down stocks
    - Crowded trades and potential reversals
    - Disconnects between sentiment and fundamentals
    """

    # System prompt defining the agent's personality and analysis approach
    SYSTEM_PROMPT = """You are a contrarian stock analyst with a skeptical but balanced approach.

Your role is to challenge conventional market wisdom by:
1. Questioning overly bullish sentiment - look for hidden risks, overcrowded trades
2. Finding opportunities in beaten-down stocks - look for overreaction, value
3. Identifying disconnects between price action and fundamentals
4. Spotting potential mean reversion opportunities

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
    "signal": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": 0.0 to 1.0,
    "score": -1.0 to 1.0,
    "reasoning": "Your contrarian analysis in 2-3 sentences",
    "factors": {
        "sentiment_disconnect": 0.0 to 1.0,
        "crowding_risk": 0.0 to 1.0,
        "mean_reversion": -1.0 to 1.0,
        "hidden_value": 0.0 to 1.0
    }
}

Score interpretation:
- score > 0.6: STRONG_BUY (contrarian bullish)
- score 0.2 to 0.6: BUY
- score -0.2 to 0.2: HOLD (no clear contrarian edge)
- score -0.6 to -0.2: SELL
- score < -0.6: STRONG_SELL (contrarian bearish)

Be concise and data-driven. Base your analysis on the provided data."""

    def __init__(
        self,
        name: str = "ClaudeContrarianAgent",
        weight: float = 1.0,
        model: str = "claude-sonnet-4-20250514",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Claude contrarian agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
            model: Claude model to use
            api_key: Anthropic API key (defaults to env var)
        """
        super().__init__(name=name, weight=weight)
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client: Optional[Anthropic] = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=60, name="claude_api"
        )

    @property
    def client(self) -> Anthropic:
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
        Perform contrarian analysis using Claude.

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

            # Call Claude API with retry
            response = self._call_claude(prompt)

            # Parse and validate response
            return self._parse_response(ticker, response)

        except Exception as e:
            self._circuit_breaker.record_failure()
            self.logger.error(f"Claude analysis failed for {ticker}: {e}")
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
            if "news_sentiment" in sentiment_data:
                prompt_parts.append(
                    f"News Sentiment: {sentiment_data['news_sentiment']:.3f}"
                )

        # Add historical context if available
        if historical_data and len(historical_data) > 0:
            prompt_parts.append("\n=== HISTORICAL CONTEXT ===")
            prompt_parts.append(f"Data points: {len(historical_data)} days")
            if len(historical_data) >= 2:
                first_price = historical_data[0].get("close", 0)
                last_price = historical_data[-1].get("close", 0)
                if first_price and last_price:
                    change = ((last_price - first_price) / first_price) * 100
                    prompt_parts.append(f"Period Change: {change:+.2f}%")

        prompt_parts.extend(
            [
                "",
                "=== YOUR TASK ===",
                "Provide your contrarian analysis. Look for:",
                "1. Are investors too bullish/bearish? Is the crowd wrong?",
                "2. Hidden risks that the market is ignoring?",
                "3. Overlooked opportunities in the data?",
                "4. Mean reversion potential?",
                "",
                "Respond with ONLY the JSON object as specified.",
            ]
        )

        return "\n".join(prompt_parts)

    @with_retry(max_retries=2, initial_delay=1.0, backoff_factor=2.0)
    def _call_claude(self, prompt: str) -> str:
        """Call Claude API with retry logic."""
        self.logger.debug(f"Calling Claude API with model {self.model}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        self._circuit_breaker.record_success()

        # Extract text from response
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
                reasoning=f"[Contrarian] {reasoning}",
                factors=factors,
                raw_score=score,
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse Claude response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}")
            return self.create_neutral_signal(ticker, f"Failed to parse AI response")
        except Exception as e:
            self.logger.error(f"Error processing Claude response: {e}")
            return self.create_neutral_signal(ticker, f"Response processing error")
