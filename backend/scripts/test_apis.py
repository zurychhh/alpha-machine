#!/usr/bin/env python3
"""
API Key Validation Script
Tests connectivity to all external APIs used by Alpha Machine

Run: python scripts/test_apis.py
"""
import os
import sys
import requests
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


def test_polygon():
    """Test Polygon.io API connection"""
    api_key = os.getenv("POLYGON_API_KEY")

    if not api_key:
        return {"status": "SKIP", "message": "POLYGON_API_KEY not configured"}

    try:
        url = f"https://api.polygon.io/v2/aggs/ticker/NVDA/prev"
        params = {"apiKey": api_key}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                price = data["results"][0]["c"]
                return {"status": "OK", "message": f"NVDA close: ${price}"}
            return {"status": "OK", "message": "Connected, but no data returned"}
        elif response.status_code == 401:
            return {"status": "FAIL", "message": "Invalid API key"}
        elif response.status_code == 429:
            return {"status": "WARN", "message": "Rate limit exceeded"}
        else:
            return {"status": "FAIL", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_finnhub():
    """Test Finnhub API connection"""
    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        return {"status": "SKIP", "message": "FINNHUB_API_KEY not configured"}

    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": "NVDA", "token": api_key}
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("c", 0) > 0:
                return {"status": "OK", "message": f"NVDA price: ${data['c']}"}
            return {"status": "WARN", "message": "Connected, but no price data"}
        elif response.status_code == 401:
            return {"status": "FAIL", "message": "Invalid API key"}
        elif response.status_code == 429:
            return {"status": "WARN", "message": "Rate limit exceeded"}
        else:
            return {"status": "FAIL", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_alphavantage():
    """Test Alpha Vantage API connection"""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        return {"status": "SKIP", "message": "ALPHA_VANTAGE_API_KEY not configured"}

    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": "NVDA",
            "apikey": api_key,
            "outputsize": "compact"
        }
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            if "Note" in data or "Information" in data:
                return {"status": "WARN", "message": "Rate limit hit (25/day)"}
            if "Time Series (Daily)" in data:
                return {"status": "OK", "message": "Historical data available"}
            if "Error Message" in data:
                return {"status": "FAIL", "message": data["Error Message"]}
            return {"status": "WARN", "message": "Unexpected response format"}
        else:
            return {"status": "FAIL", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_newsapi():
    """Test NewsAPI connection"""
    api_key = os.getenv("NEWS_API_KEY")

    if not api_key:
        return {"status": "SKIP", "message": "NEWS_API_KEY not configured"}

    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "NVDA",
            "apiKey": api_key,
            "language": "en",
            "pageSize": 1
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            total = data.get("totalResults", 0)
            return {"status": "OK", "message": f"Found {total} articles"}
        elif response.status_code == 401:
            return {"status": "FAIL", "message": "Invalid API key"}
        elif response.status_code == 429:
            return {"status": "WARN", "message": "Rate limit exceeded"}
        else:
            return {"status": "FAIL", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_reddit():
    """Test Reddit API connection (PRAW)"""
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        return {"status": "SKIP", "message": "Reddit credentials not configured"}

    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=os.getenv("REDDIT_USER_AGENT", "AlphaMachine/1.0")
        )

        # Try to access a subreddit
        subreddit = reddit.subreddit("wallstreetbets")
        hot_posts = list(subreddit.hot(limit=1))

        if hot_posts:
            return {"status": "OK", "message": f"Connected to r/wallstreetbets"}
        return {"status": "WARN", "message": "Connected, but no posts found"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_database():
    """Test PostgreSQL connection"""
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        return {"status": "SKIP", "message": "DATABASE_URL not configured"}

    try:
        import psycopg
        # Convert URL format if needed
        if db_url.startswith("postgresql://"):
            db_url_clean = db_url
        else:
            db_url_clean = db_url

        with psycopg.connect(db_url_clean) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM watchlist")
                count = cur.fetchone()[0]
                return {"status": "OK", "message": f"Connected, {count} stocks in watchlist"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def test_redis():
    """Test Redis connection"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        return {"status": "OK", "message": "Connected to Redis"}
    except Exception as e:
        return {"status": "FAIL", "message": str(e)}


def print_result(name: str, result: dict):
    """Pretty print test result"""
    status = result["status"]
    message = result["message"]

    if status == "OK":
        icon = "✅"
        color = "\033[92m"
    elif status == "WARN":
        icon = "⚠️ "
        color = "\033[93m"
    elif status == "SKIP":
        icon = "⏭️ "
        color = "\033[90m"
    else:
        icon = "❌"
        color = "\033[91m"

    reset = "\033[0m"
    print(f"{icon} {color}{name:20}{reset} {message}")


def main():
    print("\n" + "="*60)
    print("🔍 Alpha Machine - API Connection Tests")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

    print("📊 Market Data APIs:")
    print("-" * 40)
    print_result("Polygon.io", test_polygon())
    print_result("Finnhub", test_finnhub())
    print_result("Alpha Vantage", test_alphavantage())

    print("\n📰 Sentiment APIs:")
    print("-" * 40)
    print_result("NewsAPI", test_newsapi())
    print_result("Reddit (PRAW)", test_reddit())

    print("\n🗄️  Infrastructure:")
    print("-" * 40)
    print_result("PostgreSQL", test_database())
    print_result("Redis", test_redis())

    print("\n" + "="*60)
    print("Legend: ✅ OK | ⚠️  Warning | ⏭️  Skipped | ❌ Failed")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
