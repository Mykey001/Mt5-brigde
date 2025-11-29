"""
Trade history fetching from MT5
"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

def get_deals_history(days: int = 90) -> List[Dict]:
    """
    Get deal history from MT5 for the specified number of days
    
    Args:
        days: Number of days of history to fetch
        
    Returns:
        List of deal dictionaries
    """
    # Log which account we're fetching from
    account_info = mt5.account_info()
    if account_info:
        logger.info(f"Fetching deals for account: {account_info.login} ({account_info.name}) on {account_info.server}")
    else:
        logger.warning("Could not get account info - MT5 may not be connected!")
        return []
    
    from_date = datetime.now() - timedelta(days=days)
    to_date = datetime.now()
    
    logger.info(f"Fetching deals from {from_date} to {to_date} ({days} days)")
    
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals is None:
        error = mt5.last_error()
        logger.warning(f"No deals found or error: {error}")
        return []
    
    logger.info(f"MT5 returned {len(deals)} raw deals for account {account_info.login}")
    
    result = []
    for deal in deals:
        deal_dict = {
            "ticket": deal.ticket,
            "order": deal.order,
            "time": datetime.fromtimestamp(deal.time).isoformat(),
            "time_msc": deal.time_msc,
            "type": deal.type,
            "entry": deal.entry,
            "magic": deal.magic,
            "position_id": deal.position_id,
            "reason": deal.reason,
            "volume": deal.volume,
            "price": deal.price,
            "commission": deal.commission,
            "swap": deal.swap,
            "profit": deal.profit,
            "fee": deal.fee,
            "symbol": deal.symbol,
            "comment": deal.comment,
            "external_id": deal.external_id,
        }
        result.append(deal_dict)
        # Log each deal for debugging
        logger.debug(f"Deal: ticket={deal.ticket}, symbol={deal.symbol}, type={deal.type}, entry={deal.entry}, position_id={deal.position_id}, profit={deal.profit}")
    
    logger.info(f"Retrieved {len(result)} deals from MT5")
    return result


def get_orders_history(days: int = 90) -> List[Dict]:
    """
    Get order history from MT5 for the specified number of days
    
    Args:
        days: Number of days of history to fetch
        
    Returns:
        List of order dictionaries
    """
    from_date = datetime.now() - timedelta(days=days)
    to_date = datetime.now()
    
    orders = mt5.history_orders_get(from_date, to_date)
    
    if orders is None:
        logger.warning(f"No orders found or error: {mt5.last_error()}")
        return []
    
    result = []
    for order in orders:
        result.append({
            "ticket": order.ticket,
            "time_setup": datetime.fromtimestamp(order.time_setup).isoformat(),
            "time_done": datetime.fromtimestamp(order.time_done).isoformat() if order.time_done else None,
            "type": order.type,
            "state": order.state,
            "position_id": order.position_id,
            "volume_initial": order.volume_initial,
            "volume_current": order.volume_current,
            "price_open": order.price_open,
            "price_current": order.price_current,
            "price_stoplimit": order.price_stoplimit,
            "sl": order.sl,
            "tp": order.tp,
            "symbol": order.symbol,
            "comment": order.comment,
            "external_id": order.external_id,
        })
    
    logger.info(f"Retrieved {len(result)} historical orders from MT5")
    return result
