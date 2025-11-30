"""
Market data API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import logging

from ..mt5.market_data import get_candles, get_trade_context_candles
from ..mt5.manager import mt5_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["market"])


@router.get("/candles")
async def get_symbol_candles(
    symbol: str = Query(..., description="Trading symbol"),
    timeframe: str = Query("M15", description="Timeframe (M1, M5, M15, M30, H1, H4, D1)"),
    count: int = Query(100, description="Number of candles to fetch"),
    start_time: Optional[str] = Query(None, description="Start time ISO format"),
    end_time: Optional[str] = Query(None, description="End time ISO format"),
):
    """
    Get candle/OHLCV data for a symbol
    """
    if not mt5_manager._initialized:
        raise HTTPException(status_code=503, detail="MT5 not initialized")
    
    start_dt = datetime.fromisoformat(start_time) if start_time else None
    end_dt = datetime.fromisoformat(end_time) if end_time else None
    
    candles = get_candles(symbol, timeframe, start_dt, end_dt, count)
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "count": len(candles),
        "candles": candles
    }


@router.get("/trade-candles")
async def get_trade_candles(
    symbol: str = Query(..., description="Trading symbol"),
    entry_time: str = Query(..., description="Trade entry time ISO format"),
    exit_time: str = Query(..., description="Trade exit time ISO format"),
    timeframe: str = Query("M15", description="Timeframe"),
    before_candles: int = Query(50, description="Candles before entry"),
    after_candles: int = Query(20, description="Candles after exit"),
):
    """
    Get candles around a trade for context visualization
    """
    if not mt5_manager._initialized:
        raise HTTPException(status_code=503, detail="MT5 not initialized")
    
    try:
        entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
        exit_dt = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {e}")
    
    candles = get_trade_context_candles(
        symbol, entry_dt, exit_dt, timeframe, before_candles, after_candles
    )
    
    if not candles:
        raise HTTPException(
            status_code=404, 
            detail=f"No candle data found for {symbol}. Symbol may not be available."
        )
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "count": len(candles),
        "candles": candles
    }
