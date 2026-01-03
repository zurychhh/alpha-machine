"""
Sentiment Data API Endpoints
Fetch social media and news sentiment
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services.sentiment_data import sentiment_service

router = APIRouter()


@router.get("/{ticker}")
async def get_sentiment(ticker: str):
    """
    Get aggregated sentiment for a ticker

    Combines Reddit and News sentiment with weighted average:
    - Reddit: 60% weight (retail investor focus)
    - News: 40% weight

    Returns:
    - Combined sentiment score (-1 to +1)
    - Sentiment label (bullish, bearish, neutral)
    - Individual source breakdowns
    - Total mentions across sources
    """
    ticker = ticker.upper()
    sentiment = sentiment_service.aggregate_sentiment(ticker)

    return sentiment


@router.get("/{ticker}/reddit")
async def get_reddit_sentiment(ticker: str):
    """
    Get Reddit sentiment for a ticker

    Searches relevant subreddits:
    - r/wallstreetbets
    - r/stocks
    - r/investing
    - r/stockmarket

    Returns:
    - Mention count
    - Sentiment score
    - Positive/negative/neutral counts
    - Top posts with high engagement
    """
    ticker = ticker.upper()
    reddit_data = sentiment_service.get_reddit_sentiment(ticker)

    return reddit_data


@router.get("/{ticker}/news")
async def get_news_sentiment(ticker: str):
    """
    Get news sentiment for a ticker

    Fetches recent news articles and analyzes headlines

    Returns:
    - Article count
    - Sentiment score
    - Positive/negative/neutral counts
    - Recent headlines with sentiment
    """
    ticker = ticker.upper()
    news_data = sentiment_service.get_news_sentiment(ticker)

    return news_data


@router.get("/trending/reddit")
async def get_trending_tickers(
    subreddit: str = Query(default="wallstreetbets", description="Subreddit to scan"),
    limit: int = Query(default=10, ge=1, le=25, description="Number of tickers to return"),
):
    """
    Get trending tickers from a subreddit

    Scans hot posts and extracts mentioned tickers

    Returns list of tickers sorted by mention count
    """
    trending = sentiment_service.get_trending_tickers(subreddit=subreddit, limit=limit)

    return {"subreddit": subreddit, "trending_tickers": trending}
