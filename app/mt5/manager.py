import MetaTrader5 as mt5
from typing import Optional, Dict, List
from datetime import datetime
import logging
from ..models import ConnectionStatus
from ..config import settings

logger = logging.getLogger(__name__)

class MT5Manager:
    """Manages MT5 connections for multiple accounts"""
    
    def __init__(self):
        self.active_connections: Dict[int, bool] = {}  # account_id -> is_connected
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize MT5 terminal"""
        if not self._initialized:
            if not mt5.initialize():
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False
            self._initialized = True
            logger.info("MT5 initialized successfully")
        return True
    
    def shutdown(self):
        """Shutdown MT5 terminal"""
        if self._initialized:
            mt5.shutdown()
            self._initialized = False
            self.active_connections.clear()
            logger.info("MT5 shutdown")
    
    def connect_account(
        self,
        account_id: int,
        login: int,
        password: str,
        server: str,
        timeout: int = None
    ) -> tuple[bool, Optional[str]]:
        """
        Connect to MT5 account
        Returns: (success, error_message)
        """
        if not self.initialize():
            return False, "Failed to initialize MT5"
        
        timeout = timeout or settings.mt5_timeout
        
        # Disconnect current account if any
        if self.active_connections.get(account_id):
            mt5.login(login, password, server, timeout=timeout)
        
        # Attempt connection
        authorized = mt5.login(login, password, server, timeout=timeout)
        
        if not authorized:
            error = mt5.last_error()
            error_msg = f"Login failed: {error}"
            logger.error(f"Account {account_id} - {error_msg}")
            return False, error_msg
        
        self.active_connections[account_id] = True
        logger.info(f"Account {account_id} connected successfully to {server}")
        return True, None
    
    def disconnect_account(self, account_id: int):
        """Disconnect account"""
        if account_id in self.active_connections:
            del self.active_connections[account_id]
            logger.info(f"Account {account_id} disconnected")
    
    def get_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        account_info = mt5.account_info()
        if account_info is None:
            return None
        
        return {
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "margin_level": account_info.margin_level if account_info.margin > 0 else 0,
            "leverage": account_info.leverage,
            "currency": account_info.currency,
        }
    
    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        positions = mt5.positions_get()
        if positions is None:
            return []
        
        return [
            {
                "ticket": str(pos.ticket),
                "symbol": pos.symbol,
                "type": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl if pos.sl > 0 else None,
                "tp": pos.tp if pos.tp > 0 else None,
                "profit": pos.profit,
                "swap": pos.swap,
                "commission": pos.commission,
                "open_time": datetime.fromtimestamp(pos.time),
            }
            for pos in positions
        ]
    
    def get_orders(self) -> List[Dict]:
        """Get all pending orders"""
        orders = mt5.orders_get()
        if orders is None:
            return []
        
        order_types = {
            mt5.ORDER_TYPE_BUY_LIMIT: "BUY_LIMIT",
            mt5.ORDER_TYPE_SELL_LIMIT: "SELL_LIMIT",
            mt5.ORDER_TYPE_BUY_STOP: "BUY_STOP",
            mt5.ORDER_TYPE_SELL_STOP: "SELL_STOP",
            mt5.ORDER_TYPE_BUY_STOP_LIMIT: "BUY_STOP_LIMIT",
            mt5.ORDER_TYPE_SELL_STOP_LIMIT: "SELL_STOP_LIMIT",
        }
        
        return [
            {
                "ticket": str(order.ticket),
                "symbol": order.symbol,
                "type": order_types.get(order.type, "UNKNOWN"),
                "volume": order.volume_current,
                "price": order.price_open,
                "sl": order.sl if order.sl > 0 else None,
                "tp": order.tp if order.tp > 0 else None,
                "time_setup": datetime.fromtimestamp(order.time_setup),
            }
            for order in orders
        ]
    
    def is_connected(self, account_id: int) -> bool:
        """Check if account is connected"""
        return self.active_connections.get(account_id, False)

# Global instance
mt5_manager = MT5Manager()
