"""
Data Aggregation API Endpoints
Combined market and sentiment data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.data_aggregator import data_aggregator

router = APIRouter()


@router.get("/analysis/{ticker}")
async def get_comprehensive_analysis(ticker: str, db: Session = Depends(get_db)):
    """
    Get comprehensive analysis for a ticker

    Combines all data sources:
    - Real-time quote
    - Historical data summary
    - Technical indicators
    - Reddit sentiment
    - News sentiment
    - Overall outlook recommendation

    Data is cached to database for future reference
    """
    ticker = ticker.upper()

    try:
        analysis = data_aggregator.get_comprehensive_analysis(ticker, db)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to aggregate data for {ticker}: {str(e)}"
        )


@router.get("/watchlist")
async def get_watchlist_data(db: Session = Depends(get_db)):
    """
    Get all watchlist stocks with latest cached data

    Returns list of monitored stocks with:
    - Latest price
    - Latest sentiment score
    - Stock metadata (sector, tier)
    """
    try:
        watchlist = data_aggregator.get_watchlist_with_data(db)
        return {"count": len(watchlist), "stocks": watchlist}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch watchlist: {str(e)}")


@router.post("/refresh")
async def refresh_all_data(db: Session = Depends(get_db)):
    """
    Refresh data for all active watchlist stocks

    Fetches fresh market data and sentiment for all stocks.
    Use sparingly to avoid API rate limits.

    Returns summary of refresh operation
    """
    try:
        result = data_aggregator.refresh_all_data(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")
