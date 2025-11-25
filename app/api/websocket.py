from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
import asyncio
import json
import logging

from ..database import get_db, SessionLocal
from ..models import MT5Account, ConnectionStatus
from ..schemas import AccountDataUpdate, PositionResponse, OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # user_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected via WebSocket")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send message to all connections for a user"""
        if user_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected
        for conn in disconnected:
            self.active_connections[user_id].discard(conn)
    
    async def broadcast_account_update(self, account: MT5Account):
        """Broadcast account data update to user"""
        message = {
            "type": "account_update",
            "data": {
                "account_id": account.id,
                "balance": account.balance,
                "equity": account.equity,
                "margin": account.margin,
                "free_margin": account.free_margin,
                "margin_level": account.margin_level,
                "status": account.status.value,
                "last_sync": account.last_sync.isoformat() if account.last_sync else None,
                "positions": [
                    {
                        "ticket": pos.ticket,
                        "symbol": pos.symbol,
                        "type": pos.type,
                        "volume": pos.volume,
                        "open_price": pos.open_price,
                        "current_price": pos.current_price,
                        "profit": pos.profit,
                        "sl": pos.sl,
                        "tp": pos.tp,
                    }
                    for pos in account.positions
                ],
                "orders": [
                    {
                        "ticket": order.ticket,
                        "symbol": order.symbol,
                        "type": order.type,
                        "volume": order.volume,
                        "price": order.price,
                        "sl": order.sl,
                        "tp": order.tp,
                    }
                    for order in account.orders
                ]
            }
        }
        await self.send_to_user(account.user_id, message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time updates
    Client connects with user_id and receives updates for all their accounts
    """
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial data for all user accounts
        db = SessionLocal()
        try:
            accounts = db.query(MT5Account).filter(
                MT5Account.user_id == user_id
            ).all()
            
            for account in accounts:
                await manager.broadcast_account_update(account)
        finally:
            db.close()
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle ping/pong or other client messages
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                break
    
    finally:
        manager.disconnect(websocket, user_id)

# Function to be called by sync worker
async def notify_account_update(account_id: int):
    """Called after account sync to push updates via WebSocket"""
    db = SessionLocal()
    try:
        account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
        if account:
            await manager.broadcast_account_update(account)
    finally:
        db.close()
