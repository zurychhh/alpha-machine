"""
Sentiment Data Service
Aggregates sentiment from Reddit, Twitter, and News sources

Uses VADER (Valence Aware Dictionary for sEntiment Reasoning) for
accurate financial text sentiment analysis.
"""

import json
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize VADER - lazy load to avoid import errors during testing
_vader_analyzer = None


def get_vader_analyzer():
    """Lazy-load VADER analyzer to avoid import errors."""
    global _vader_analyzer
    if _vader_analyzer is None:
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            _vader_analyzer = SentimentIntensityAnalyzer()
            logger.info("VADER sentiment analyzer initialized")
        except ImportError:
            logger.warning("vaderSentiment not installed, using fallback")
            _vader_analyzer = None
    return _vader_analyzer


def _make_request_with_retry(
    url: str,
    params: Dict,
    timeout: int = 10,
    max_retries: int = 3,
) -> Optional[requests.Response]:
    """
    Make an HTTP request with retry logic for transient failures.

    Args:
        url: Request URL
        params: Query parameters
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Response object or None on failure
    """
    delay = 1.0

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            # Handle rate limiting
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    retry_after = int(response.headers.get("Retry-After", delay))
                    logger.warning(
                        f"Rate limited, waiting {retry_after}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_after)
                    delay *= 2
                    continue

            # Handle server errors
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Server error {response.status_code}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

            return response

        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Request timeout, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Request timeout after {max_retries} attempts: {e}")
                return None

        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Connection error, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Connection error after {max_retries} attempts: {e}")
                return None

        except Exception as e:
            logger.error(f"Unexpected request error: {type(e).__name__}: {e}")
            return None

    return None


class SentimentDataService:
    """Aggregate sentiment from multiple social/news sources"""

    # Cache TTL in seconds (30 minutes)
    CACHE_TTL = 1800

    def __init__(self):
        self.reddit = None
        self.vader = get_vader_analyzer()
        self._init_reddit()

    def _get_cached_sentiment(self, ticker: str) -> Optional[Dict]:
        """
        Check Redis cache for sentiment data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Cached sentiment data or None if not found
        """
        if not settings.REDIS_URL:
            return None

        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            cached = r.get(f"sentiment:{ticker}")
            if cached:
                logger.debug(f"Cache hit for sentiment:{ticker}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
        return None

    def _cache_sentiment(self, ticker: str, data: Dict):
        """
        Cache sentiment data to Redis.

        Args:
            ticker: Stock ticker symbol
            data: Sentiment data to cache
        """
        if not settings.REDIS_URL:
            return

        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            r.setex(f"sentiment:{ticker}", self.CACHE_TTL, json.dumps(data))
            logger.debug(f"Cached sentiment for {ticker} (TTL={self.CACHE_TTL}s)")
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

    def _init_reddit(self):
        """Initialize Reddit API client (PRAW)"""
        if not all([settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET]):
            logger.warning("Reddit API credentials not configured")
            return

        try:
            import praw

            self.reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            logger.info("Reddit API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Reddit: {e}")
            self.reddit = None

    def get_reddit_sentiment(self, ticker: str) -> Dict:
        """
        Scrape Reddit mentions and calculate sentiment

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with Reddit sentiment data
        """
        result = {
            "source": "reddit",
            "ticker": ticker,
            "mentions": 0,
            "sentiment_score": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "top_posts": [],
            "timestamp": datetime.now().isoformat(),
        }

        if not self.reddit:
            logger.warning("Reddit client not available")
            return result

        try:
            mentions = 0
            positive = 0
            negative = 0
            neutral = 0
            top_posts = []

            # Search relevant subreddits
            subreddits = ["wallstreetbets", "stocks", "investing", "stockmarket"]

            sentiment_sum = 0.0

            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Search last 24 hours
                    for submission in subreddit.search(ticker, time_filter="day", limit=25):
                        mentions += 1

                        # VADER-based sentiment analysis (returns -1.0 to 1.0)
                        sentiment = self._analyze_reddit_post(submission)
                        sentiment_sum += sentiment

                        # Classify based on compound score thresholds
                        if sentiment >= 0.05:
                            positive += 1
                        elif sentiment <= -0.05:
                            negative += 1
                        else:
                            neutral += 1

                        # Track top posts
                        if submission.score > 50 and len(top_posts) < 5:
                            top_posts.append(
                                {
                                    "title": submission.title[:100],
                                    "score": submission.score,
                                    "subreddit": subreddit_name,
                                    "sentiment": round(sentiment, 3),
                                }
                            )

                except Exception as e:
                    logger.warning(f"Error searching r/{subreddit_name}: {e}")
                    continue

            # Calculate average sentiment score (-1 to +1)
            if mentions > 0:
                sentiment_score = sentiment_sum / mentions
            else:
                sentiment_score = 0.0

            result.update(
                {
                    "mentions": mentions,
                    "sentiment_score": round(sentiment_score, 3),
                    "positive_count": positive,
                    "negative_count": negative,
                    "neutral_count": neutral,
                    "top_posts": top_posts,
                }
            )

            logger.info(
                f"Reddit sentiment for {ticker}: {mentions} mentions, score={sentiment_score:.2f}"
            )

        except Exception as e:
            logger.error(f"Reddit sentiment failed for {ticker}: {e}")

        return result

    def _analyze_reddit_post(self, submission) -> float:
        """
        Analyze Reddit post sentiment using VADER.

        Args:
            submission: Reddit submission object

        Returns:
            Compound sentiment score (-1.0 to 1.0)
        """
        # Build text from title and selftext
        text = submission.title
        if hasattr(submission, 'selftext') and submission.selftext:
            # Limit selftext to avoid processing huge posts
            text += " " + submission.selftext[:500]

        # Use VADER if available
        if self.vader:
            scores = self.vader.polarity_scores(text)
            compound = scores['compound']

            # Engagement boost: high score + high upvote ratio = community agreement
            if submission.score > 100 and submission.upvote_ratio > 0.8:
                compound = min(compound + 0.1, 1.0)
            elif submission.score < 0:
                # Negative score indicates community disagrees with sentiment
                compound = max(compound - 0.1, -1.0)

            return compound

        # Fallback to simple keyword analysis if VADER not available
        title = submission.title.lower()

        positive_keywords = [
            "buy", "bullish", "moon", "rocket", "gain", "profit", "calls",
            "long", "undervalued", "breakout", "surge", "beat", "upgrade",
        ]
        negative_keywords = [
            "sell", "bearish", "crash", "dump", "loss", "puts", "short",
            "overvalued", "downgrade", "weak", "miss", "plunge", "drop",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in title)
        negative_count = sum(1 for kw in negative_keywords if kw in title)

        if submission.score > 100 and submission.upvote_ratio > 0.8:
            positive_count += 1
        elif submission.score < 0:
            negative_count += 1

        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        return 0.0

    def get_news_sentiment(self, ticker: str) -> Dict:
        """
        Fetch news and analyze sentiment

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with news sentiment data
        """
        result = {
            "source": "news",
            "ticker": ticker,
            "article_count": 0,
            "sentiment_score": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "headlines": [],
            "timestamp": datetime.now().isoformat(),
        }

        if not settings.NEWS_API_KEY:
            logger.warning("NewsAPI key not configured")
            return result

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": ticker,
                "apiKey": settings.NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 30,
            }

            response = _make_request_with_retry(url, params, timeout=10, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])

                if not articles:
                    logger.info(f"No news articles found for {ticker}")
                    return result

                positive = 0
                negative = 0
                neutral = 0
                headlines = []
                sentiment_sum = 0.0

                for article in articles:
                    title = article.get("title", "")
                    if not title:
                        continue

                    # VADER-based sentiment analysis (returns -1.0 to 1.0)
                    sentiment = self._analyze_headline(title)
                    sentiment_sum += sentiment

                    # Classify based on compound score thresholds
                    if sentiment >= 0.05:
                        positive += 1
                    elif sentiment <= -0.05:
                        negative += 1
                    else:
                        neutral += 1

                    # Store headlines with sentiment
                    if len(headlines) < 10:
                        headlines.append(
                            {
                                "title": title[:150],
                                "source": article.get("source", {}).get("name", "Unknown"),
                                "published": article.get("publishedAt", ""),
                                "sentiment": round(sentiment, 3),
                            }
                        )

                total = len(articles)
                sentiment_score = sentiment_sum / total if total > 0 else 0.0

                result.update(
                    {
                        "article_count": total,
                        "sentiment_score": round(sentiment_score, 3),
                        "positive_count": positive,
                        "negative_count": negative,
                        "neutral_count": neutral,
                        "headlines": headlines,
                    }
                )

                logger.info(
                    f"News sentiment for {ticker}: {total} articles, score={sentiment_score:.2f}"
                )

            elif response.status_code == 401:
                logger.error("NewsAPI authentication failed - check API key")
            elif response.status_code == 429:
                logger.warning("NewsAPI rate limit exceeded")
            else:
                logger.warning(f"NewsAPI error: {response.status_code}")

        except Exception as e:
            logger.error(f"News sentiment failed for {ticker}: {e}")

        return result

    def _analyze_headline(self, headline: str) -> float:
        """
        Analyze news headline sentiment using VADER.

        Args:
            headline: News headline text

        Returns:
            Compound sentiment score (-1.0 to 1.0)
        """
        # Use VADER if available
        if self.vader:
            scores = self.vader.polarity_scores(headline)
            return scores['compound']

        # Fallback to keyword analysis
        headline_lower = headline.lower()

        positive_keywords = [
            "surge", "rally", "gain", "bullish", "upgrade", "beat", "record",
            "soar", "jump", "rise", "growth", "profit", "breakthrough",
        ]
        negative_keywords = [
            "plunge", "drop", "bearish", "downgrade", "miss", "crash", "fall",
            "decline", "loss", "concern", "warning", "cut", "layoff", "lawsuit",
        ]

        positive_count = sum(1 for kw in positive_keywords if kw in headline_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in headline_lower)

        if positive_count > negative_count:
            return 0.5
        elif negative_count > positive_count:
            return -0.5
        return 0.0

    def aggregate_sentiment(self, ticker: str, use_cache: bool = True) -> Dict:
        """
        Combine all sentiment sources into weighted average.

        Args:
            ticker: Stock ticker symbol
            use_cache: Whether to use Redis caching (default: True)

        Returns:
            Dictionary with combined sentiment data
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached_sentiment(ticker)
            if cached:
                logger.info(f"Using cached sentiment for {ticker}")
                cached["from_cache"] = True
                return cached

        reddit_data = self.get_reddit_sentiment(ticker)
        news_data = self.get_news_sentiment(ticker)

        # Weighted average (Reddit 60%, News 40%)
        # Reddit gets higher weight due to retail investor focus
        reddit_score = reddit_data.get("sentiment_score", 0)
        news_score = news_data.get("sentiment_score", 0)

        # Adjust weights based on data availability
        reddit_weight = 0.6 if reddit_data.get("mentions", 0) > 0 else 0
        news_weight = 0.4 if news_data.get("article_count", 0) > 0 else 0

        total_weight = reddit_weight + news_weight
        if total_weight > 0:
            combined_score = (
                reddit_score * reddit_weight + news_score * news_weight
            ) / total_weight
        else:
            combined_score = 0.0

        # Determine sentiment label
        if combined_score > 0.3:
            sentiment_label = "bullish"
        elif combined_score > 0.1:
            sentiment_label = "slightly_bullish"
        elif combined_score < -0.3:
            sentiment_label = "bearish"
        elif combined_score < -0.1:
            sentiment_label = "slightly_bearish"
        else:
            sentiment_label = "neutral"

        result = {
            "ticker": ticker,
            "combined_sentiment": round(combined_score, 3),
            "sentiment_label": sentiment_label,
            "reddit": reddit_data,
            "news": news_data,
            "total_mentions": reddit_data.get("mentions", 0) + news_data.get("article_count", 0),
            "timestamp": datetime.now().isoformat(),
            "from_cache": False,
        }

        logger.info(f"Combined sentiment for {ticker}: {combined_score:.2f} ({sentiment_label})")

        # Cache the result for future requests
        if use_cache:
            self._cache_sentiment(ticker, result)

        return result

    def get_trending_tickers(
        self, subreddit: str = "wallstreetbets", limit: int = 10
    ) -> List[Dict]:
        """
        Get trending tickers from a subreddit

        Args:
            subreddit: Subreddit name
            limit: Number of tickers to return

        Returns:
            List of trending tickers with mention counts
        """
        if not self.reddit:
            return []

        try:
            ticker_counts = {}
            sub = self.reddit.subreddit(subreddit)

            # Common stock ticker pattern (1-5 uppercase letters)
            import re

            ticker_pattern = re.compile(r"\b([A-Z]{1,5})\b")

            # Exclude common words that look like tickers
            exclude = {
                "I",
                "A",
                "THE",
                "AND",
                "FOR",
                "TO",
                "OF",
                "IS",
                "IT",
                "ON",
                "IN",
                "AT",
                "BE",
                "OR",
                "AS",
                "IF",
                "SO",
                "BY",
                "CEO",
                "IPO",
                "ETF",
                "USD",
                "USA",
                "SEC",
                "FDA",
                "CEO",
            }

            for submission in sub.hot(limit=50):
                title = submission.title
                matches = ticker_pattern.findall(title)

                for ticker in matches:
                    if ticker not in exclude:
                        ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

            # Sort by count and return top tickers
            sorted_tickers = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

            return [{"ticker": t, "mentions": c} for t, c in sorted_tickers]

        except Exception as e:
            logger.error(f"Failed to get trending tickers: {e}")
            return []


# Singleton instance
sentiment_service = SentimentDataService()
