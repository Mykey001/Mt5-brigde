import MetaTrader5 as mt5
from typing import Optional, Dict, List
from datetime import datetime
import logging
import time
import subprocess
import os
from ..models import ConnectionStatus
from ..config import settings

logger = logging.getLogger(__name__)

class MT5Manager:
    """Manages MT5 connections for multiple accounts"""
    
    def __init__(self):
        self.active_connections: Dict[int, bool] = {}  # account_id -> is_connected
        self._initialized = False
    
    def _ensure_mt5_running(self):
        """Ensure MT5 terminal is running"""
        try:
            # Check if MT5 is running
            result = subprocess.run(
                ['powershell', '-Command', 'Get-Process terminal64 -ErrorAction SilentlyContinue'],
                capture_output=True, text=True, timeout=10
            )
            if 'terminal64' not in result.stdout:
                # Start MT5 terminal
                logger.info("Starting MT5 terminal...")
                subprocess.Popen([settings.mt5_path], shell=False)
                time.sleep(5)  # Wait for MT5 to start
        except Exception as e:
            logger.warning(f"Could not check/start MT5: {e}")
    
    def initialize(self) -> bool:
        """Initialize MT5 terminal (basic init without login)"""
        if not self._initialized:
            self._ensure_mt5_running()
            try:
                if mt5.initialize(path=settings.mt5_path):
                    self._initialized = True
                    logger.info("MT5 initialized successfully")
                    return True
                else:
                    logger.warning(f"MT5 basic init failed: {mt5.last_error()}, will init on connect")
                    return True
            except Exception as e:
                logger.warning(f"MT5 init exception: {e}")
                return True
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
        timeout = timeout or settings.mt5_timeout
        
        # Ensure MT5 is running
        self._ensure_mt5_running()
        
        # Shutdown any existing connection first
        mt5.shutdown()
        time.sleep(1)
        
        # Try multiple connection approaches
        # Approach 1: Initialize with all credentials at once
        logger.info(f"Attempting to connect account {login} to {server}...")
        
        if mt5.initialize(path=settings.mt5_path, login=login, password=password, server=server, timeout=timeout):
            self._initialized = True
            self.active_connections[account_id] = True
            logger.info(f"Account {account_id} connected successfully to {server}")
            return True, None
        
        error1 = mt5.last_error()
        logger.warning(f"First attempt failed: {error1}")
        
        # Approach 2: Initialize first, then login separately
        mt5.shutdown()
        time.sleep(1)
        
        if mt5.initialize(path=settings.mt5_path):
            logger.info("MT5 initialized, attempting login...")
            if mt5.login(login, password, server, timeout=timeout):
                self._initialized = True
                self.active_connections[account_id] = True
                logger.info(f"Account {account_id} connected successfully to {server}")
                return True, None
            error2 = mt5.last_error()
            logger.warning(f"Login attempt failed: {error2}")
        else:
            error2 = mt5.last_error()
            logger.warning(f"Second init failed: {error2}")
        
        # Both approaches failed
        error_msg = f"Login failed: {error1}"
        logger.error(f"Account {account_id} - {error_msg}")
        return False, error_msg
    
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
