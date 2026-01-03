"""
Multi-Modal Agent - Synthesis Analysis
Uses Google Gemini Flash for multi-perspective synthesis.
Combines technical, fundamental, and sentiment perspectives.
"""

import os
import json
from typing import Dict, Optional, List
import google.generativeai as genai
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.core.retry import with_retry, CircuitBreaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MultiModalAgent(BaseAgent):
    """
    Multi-modal analyst agent powered by Google Gemini Flash.

    This agent synthesizes multiple perspectives:
    - Technical analysis (RSI, moving averages, trends)
    - Sentiment analysis (news, social media)
    - Fundamental context
    - Cross-validation of signals
    """

    SYSTEM_PROMPT = """You are a multi-modal AI analyst synthesizing technical, fundamental, and sentiment data.

Your synthesis approach:
1. Technical: RSI trends, moving averages, price action
2. Sentiment: News tone, social media mood
3. Synthesis: Combine all perspectives for a unified view
4. Confidence: Higher when all signals align

IMPORTANT: You must respond with ONLY valid JSON in this exact format:
{
    "signal": "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL",
    "confidence": 0.0 to 1.0,
    "score": -1.0 to 1.0,
    "reasoning": "Your multi-modal synthesis in 2-3 sentences",
    "factors": {
        "technical_score": -1.0 to 1.0,
        "sentiment_score": -1.0 to 1.0,
        "alignment_score": 0.0 to 1.0,
        "synthesis_confidence": 0.0 to 1.0
    }
}

Score interpretation:
- score > 0.6: STRONG_BUY (all perspectives bullish)
- score 0.2 to 0.6: BUY (mostly bullish signals)
- score -0.2 to 0.2: HOLD (mixed or conflicting signals)
- score -0.6 to -0.2: SELL (mostly bearish signals)
- score < -0.6: STRONG_SELL (all perspectives bearish)

Key principle: Confidence is HIGHEST when technical and sentiment ALIGN.
When they conflict, reduce confidence and favor HOLD."""

    def __init__(
        self,
        name: str = "MultiModalAgent",
        weight: float = 1.0,
        model: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
    ):
        """
        Initialize the multi-modal agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
            model: Gemini model to use
            api_key: Google AI API key (defaults to env var)
        """
        super().__init__(name=name, weight=weight)
        self.model_name = model
        self.api_key = api_key or settings.GOOGLE_AI_API_KEY
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
        Perform multi-modal synthesis using Gemini.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data (price, volume, indicators)
            sentiment_data: Sentiment analysis data
            historical_data: Historical price data

        Returns:
            AgentSignal with synthesized recommendation
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
            self.logger.error(f"MultiModal analysis failed for {ticker}: {e}")
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
            f"Analyze {ticker} using MULTI-MODAL synthesis.",
            "",
            "=== TECHNICAL DATA ===",
            f"Ticker: {ticker}",
            f"Current Price: ${current_price}",
        ]

        # Technical perspective
        if indicators:
            prompt_parts.append("\n--- Technical Indicators ---")
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                prompt_parts.append(f"RSI: {rsi:.1f}")
                if rsi < 30:
                    prompt_parts.append("  Technical: OVERSOLD")
                elif rsi > 70:
                    prompt_parts.append("  Technical: OVERBOUGHT")
                else:
                    prompt_parts.append("  Technical: NEUTRAL")

            if "price_change_7d" in indicators:
                prompt_parts.append(f"7-Day Change: {indicators['price_change_7d']:+.2f}%")
            if "price_change_30d" in indicators:
                prompt_parts.append(f"30-Day Change: {indicators['price_change_30d']:+.2f}%")
            if "volume_trend" in indicators:
                prompt_parts.append(f"Volume Trend: {indicators['volume_trend']}")
            if "sma_50" in indicators:
                prompt_parts.append(f"50-Day SMA: ${indicators['sma_50']:.2f}")
            if "sma_200" in indicators:
                prompt_parts.append(f"200-Day SMA: ${indicators['sma_200']:.2f}")

        # Sentiment perspective
        prompt_parts.append("\n=== SENTIMENT DATA ===")
        if sentiment_data:
            if "combined_sentiment" in sentiment_data:
                sentiment = sentiment_data["combined_sentiment"]
                prompt_parts.append(f"Combined Sentiment: {sentiment:.3f}")
                if sentiment > 0.3:
                    prompt_parts.append("  Sentiment: BULLISH")
                elif sentiment < -0.3:
                    prompt_parts.append("  Sentiment: BEARISH")
                else:
                    prompt_parts.append("  Sentiment: NEUTRAL")
            if "sentiment_label" in sentiment_data:
                prompt_parts.append(f"Sentiment Label: {sentiment_data['sentiment_label']}")
            if "total_mentions" in sentiment_data:
                mentions = sentiment_data["total_mentions"]
                prompt_parts.append(f"Total Mentions: {mentions}")
                if mentions > 50:
                    prompt_parts.append("  Attention: HIGH")
                elif mentions < 10:
                    prompt_parts.append("  Attention: LOW")
        else:
            prompt_parts.append("No sentiment data available")

        # Historical context
        if historical_data and len(historical_data) > 0:
            prompt_parts.append("\n=== HISTORICAL CONTEXT ===")
            prompt_parts.append(f"Data points: {len(historical_data)} days")

            if len(historical_data) >= 5:
                closes = [d.get("close", 0) for d in historical_data if d.get("close")]
                if len(closes) >= 5:
                    recent = closes[-5:]
                    trend = "upward" if recent[-1] > recent[0] else "downward"
                    prompt_parts.append(f"Recent 5-day trend: {trend}")

        # Synthesis task
        prompt_parts.extend([
            "",
            "=== YOUR MULTI-MODAL TASK ===",
            "Synthesize all perspectives:",
            "1. What does the technical data suggest?",
            "2. What does sentiment indicate?",
            "3. Do they ALIGN or CONFLICT?",
            "4. If aligned: HIGH confidence signal",
            "5. If conflicting: LOW confidence or HOLD",
            "",
            "Respond with ONLY the JSON object as specified."
        ])

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
                reasoning=f"[MultiModal] {reasoning}",
                factors=factors,
                raw_score=score,
            )

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse Gemini response: {e}")
            self.logger.debug(f"Raw response: {response[:500]}")
            return self.create_neutral_signal(ticker, "Failed to parse AI response")
        except Exception as e:
            self.logger.error(f"Error processing Gemini response: {e}")
            return self.create_neutral_signal(ticker, "Response processing error")
