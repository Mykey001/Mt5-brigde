"""
Market data fetching from MT5 - candles, rates, etc.
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# MT5 Timeframe mapping
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def get_candles(
    symbol: str,
    timeframe: str = "M15",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    count: int = 100
) -> List[Dict]:
    """
    Get candle/OHLCV data from MT5
    
    Args:
        symbol: Trading symbol (e.g., "EURUSD", "XAUUSD")
        timeframe: Timeframe string (M1, M5, M15, M30, H1, H4, D1, W1, MN1)
        start_time: Start datetime for the range
        end_time: End datetime for the range
        count: Number of candles to fetch if no time range specified
        
    Returns:
        List of candle dictionaries with OHLCV data
    """
    tf = TIMEFRAME_MAP.get(timeframe.upper(), mt5.TIMEFRAME_M15)
    
    logger.info(f"Fetching candles for {symbol}, timeframe={timeframe}, count={count}")
    
    # Check if symbol exists
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        # Try with common suffixes
        for suffix in [".m", ".std", "", "m", "pro"]:
            test_symbol = f"{symbol}{suffix}" if suffix else symbol
            symbol_info = mt5.symbol_info(test_symbol)
            if symbol_info is not None:
                symbol = test_symbol
                logger.info(f"Found symbol with suffix: {symbol}")
                break
    
    if symbol_info is None:
        logger.warning(f"Symbol {symbol} not found")
        return []
    
    # Ensure symbol is selected for market watch
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            logger.warning(f"Failed to select symbol {symbol}")
            return []
    
    rates = None
    
    if start_time and end_time:
        # Fetch by time range
        rates = mt5.copy_rates_range(symbol, tf, start_time, end_time)
    elif start_time:
        # Fetch from start_time to now
        rates = mt5.copy_rates_range(symbol, tf, start_time, datetime.now())
    else:
        # Fetch last N candles
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    
    if rates is None or len(rates) == 0:
        error = mt5.last_error()
        logger.warning(f"No rates found for {symbol}: {error}")
        return []
    
    logger.info(f"Retrieved {len(rates)} candles for {symbol}")
    
    result = []
    for rate in rates:
        result.append({
            "time": datetime.fromtimestamp(rate['time']).isoformat(),
            "timestamp": int(rate['time']),
            "open": float(rate['open']),
            "high": float(rate['high']),
            "low": float(rate['low']),
            "close": float(rate['close']),
            "volume": int(rate['tick_volume']),
            "spread": int(rate['spread']) if 'spread' in rate.dtype.names else 0,
        })
    
    return result


def get_trade_context_candles(
    symbol: str,
    entry_time: datetime,
    exit_time: datetime,
    timeframe: str = "M15",
    before_candles: int = 50,
    after_candles: int = 20
) -> List[Dict]:
    """
    Get candles around a trade for context visualization
    
    Args:
        symbol: Trading symbol
        entry_time: Trade entry datetime
        exit_time: Trade exit datetime
        timeframe: Timeframe string
        before_candles: Number of candles to fetch before entry
        after_candles: Number of candles to fetch after exit
        
    Returns:
        List of candle dictionaries
    """
    tf = TIMEFRAME_MAP.get(timeframe.upper(), mt5.TIMEFRAME_M15)
    
    # Calculate time offsets based on timeframe
    tf_minutes = {
        "M1": 1, "M5": 5, "M15": 15, "M30": 30,
        "H1": 60, "H4": 240, "D1": 1440, "W1": 10080, "MN1": 43200
    }
    minutes = tf_minutes.get(timeframe.upper(), 15)
    
    # Calculate start and end times with buffer
    start_time = entry_time - timedelta(minutes=minutes * before_candles)
    end_time = exit_time + timedelta(minutes=minutes * after_candles)
    
    logger.info(f"Fetching trade context candles for {symbol} from {start_time} to {end_time}")
    
    return get_candles(symbol, timeframe, start_time, end_time)
