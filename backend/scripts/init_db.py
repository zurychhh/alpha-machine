#!/usr/bin/env python3
"""Initialize database tables and seed watchlist"""
import sys
sys.path.insert(0, '/app')

from app.core.database import Base, engine, SessionLocal
from app.models.signal import Signal
from app.models.watchlist import Watchlist

# Default AI stocks to track
DEFAULT_STOCKS = [
    {"ticker": "NVDA", "company_name": "NVIDIA Corporation", "sector": "Technology"},
    {"ticker": "AAPL", "company_name": "Apple Inc.", "sector": "Technology"},
    {"ticker": "MSFT", "company_name": "Microsoft Corporation", "sector": "Technology"},
    {"ticker": "GOOGL", "company_name": "Alphabet Inc.", "sector": "Technology"},
    {"ticker": "TSLA", "company_name": "Tesla, Inc.", "sector": "Automotive"},
    {"ticker": "AMD", "company_name": "Advanced Micro Devices", "sector": "Technology"},
    {"ticker": "META", "company_name": "Meta Platforms, Inc.", "sector": "Technology"},
    {"ticker": "AMZN", "company_name": "Amazon.com, Inc.", "sector": "Consumer"},
    {"ticker": "PLTR", "company_name": "Palantir Technologies", "sector": "Technology"},
    {"ticker": "CRM", "company_name": "Salesforce, Inc.", "sector": "Technology"},
]

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def seed_watchlist():
    """Seed watchlist with default stocks"""
    db = SessionLocal()
    try:
        existing = db.query(Watchlist).count()
        if existing > 0:
            print(f"Watchlist already has {existing} stocks, skipping seed.")
            return

        print("Seeding watchlist with default stocks...")
        for stock in DEFAULT_STOCKS:
            watchlist_item = Watchlist(
                ticker=stock["ticker"],
                company_name=stock["company_name"],
                sector=stock["sector"],
                tier=1,
                active=True
            )
            db.add(watchlist_item)

        db.commit()
        print(f"Added {len(DEFAULT_STOCKS)} stocks to watchlist!")
    except Exception as e:
        print(f"Error seeding watchlist: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_watchlist()
