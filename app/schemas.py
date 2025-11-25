from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .models import ConnectionStatus

# Account Schemas
class AccountCreate(BaseModel):
    user_id: int
    broker_name: str
    account_number: str
    password: str
    server: str

class AccountUpdate(BaseModel):
    password: Optional[str] = None
    server: Optional[str] = None

class AccountResponse(BaseModel):
    id: int
    user_id: int
    broker_name: str
    account_number: str
    server: str
    status: ConnectionStatus
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    leverage: int
    currency: str
    last_connected: Optional[datetime]
    last_sync: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

# Position Schemas
class PositionResponse(BaseModel):
    id: int
    ticket: str
    symbol: str
    type: str
    volume: float
    open_price: float
    current_price: float
    sl: Optional[float]
    tp: Optional[float]
    profit: float
    swap: float
    commission: float
    open_time: datetime
    
    class Config:
        from_attributes = True

# Order Schemas
class OrderResponse(BaseModel):
    id: int
    ticket: str
    symbol: str
    type: str
    volume: float
    price: float
    sl: Optional[float]
    tp: Optional[float]
    time_setup: datetime
    
    class Config:
        from_attributes = True

# WebSocket Messages
class WSMessage(BaseModel):
    type: str
    data: dict

class AccountDataUpdate(BaseModel):
    account_id: int
    balance: float
    equity: float
    margin: float
    free_margin: float
    positions: List[PositionResponse]
    orders: List[OrderResponse]

# Broker/Server Selection
class BrokerServer(BaseModel):
    name: str
    description: Optional[str] = None

class BrokerInfo(BaseModel):
    broker_name: str
    display_name: str
    servers: List[BrokerServer]
