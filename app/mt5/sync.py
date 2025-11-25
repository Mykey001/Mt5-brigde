from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging
from ..models import MT5Account, Position, Order, ConnectionStatus
from .manager import mt5_manager
from ..security import decrypt_credentials

logger = logging.getLogger(__name__)

class DataSyncService:
    """Handles syncing data between MT5 and database"""
    
    @staticmethod
    def sync_account(account: MT5Account, db: Session) -> bool:
        """
        Sync single account data from MT5 to database
        Returns True if successful
        """
        try:
            # Decrypt credentials
            password = decrypt_credentials(account.encrypted_password)
            
            # Connect to MT5
            success, error = mt5_manager.connect_account(
                account.id,
                int(account.account_number),
                password,
                account.server
            )
            
            if not success:
                account.status = ConnectionStatus.ERROR
                account.error_message = error
                db.commit()
                return False
            
            # Update connection status
            account.status = ConnectionStatus.CONNECTED
            account.last_connected = datetime.utcnow()
            account.error_message = None
            
            # Sync account info
            account_info = mt5_manager.get_account_info()
            if account_info:
                account.balance = account_info["balance"]
                account.equity = account_info["equity"]
                account.margin = account_info["margin"]
                account.free_margin = account_info["free_margin"]
                account.margin_level = account_info["margin_level"]
                account.leverage = account_info["leverage"]
                account.currency = account_info["currency"]
            
            # Sync positions
            DataSyncService._sync_positions(account, db)
            
            # Sync orders
            DataSyncService._sync_orders(account, db)
            
            account.last_sync = datetime.utcnow()
            db.commit()
            
            logger.info(f"Account {account.id} synced successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing account {account.id}: {e}")
            account.status = ConnectionStatus.ERROR
            account.error_message = str(e)
            db.commit()
            return False
    
    @staticmethod
    def _sync_positions(account: MT5Account, db: Session):
        """Sync positions for account"""
        mt5_positions = mt5_manager.get_positions()
        mt5_tickets = {pos["ticket"] for pos in mt5_positions}
        
        # Remove closed positions
        db.query(Position).filter(
            Position.account_id == account.id,
            ~Position.ticket.in_(mt5_tickets) if mt5_tickets else True
        ).delete(synchronize_session=False)
        
        # Update or create positions
        for pos_data in mt5_positions:
            position = db.query(Position).filter(
                Position.ticket == pos_data["ticket"]
            ).first()
            
            if position:
                # Update existing
                position.current_price = pos_data["current_price"]
                position.profit = pos_data["profit"]
                position.swap = pos_data["swap"]
                position.commission = pos_data["commission"]
            else:
                # Create new
                position = Position(
                    account_id=account.id,
                    ticket=pos_data["ticket"],
                    symbol=pos_data["symbol"],
                    type=pos_data["type"],
                    volume=pos_data["volume"],
                    open_price=pos_data["open_price"],
                    current_price=pos_data["current_price"],
                    sl=pos_data["sl"],
                    tp=pos_data["tp"],
                    profit=pos_data["profit"],
                    swap=pos_data["swap"],
                    commission=pos_data["commission"],
                    open_time=pos_data["open_time"]
                )
                db.add(position)
    
    @staticmethod
    def _sync_orders(account: MT5Account, db: Session):
        """Sync pending orders for account"""
        mt5_orders = mt5_manager.get_orders()
        mt5_tickets = {order["ticket"] for order in mt5_orders}
        
        # Remove cancelled/filled orders
        db.query(Order).filter(
            Order.account_id == account.id,
            ~Order.ticket.in_(mt5_tickets) if mt5_tickets else True
        ).delete(synchronize_session=False)
        
        # Update or create orders
        for order_data in mt5_orders:
            order = db.query(Order).filter(
                Order.ticket == order_data["ticket"]
            ).first()
            
            if not order:
                # Create new
                order = Order(
                    account_id=account.id,
                    ticket=order_data["ticket"],
                    symbol=order_data["symbol"],
                    type=order_data["type"],
                    volume=order_data["volume"],
                    price=order_data["price"],
                    sl=order_data["sl"],
                    tp=order_data["tp"],
                    time_setup=order_data["time_setup"]
                )
                db.add(order)

sync_service = DataSyncService()
