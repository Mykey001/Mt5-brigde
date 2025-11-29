from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ConnectionStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"

class MT5Account(Base):
    __tablename__ = "mt5_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # Your web app user ID
    broker_name = Column(String(100), nullable=False)  # XM, Exness, etc
    account_number = Column(String(50), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    server = Column(String(100), nullable=False)
    
    # Connection status
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.DISCONNECTED)
    last_connected = Column(DateTime, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Account info (synced from MT5)
    account_name = Column(String(200), nullable=True)  # Account holder's name from MT5
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    free_margin = Column(Float, default=0.0)
    margin_level = Column(Float, default=0.0)
    leverage = Column(Integer, default=0)
    currency = Column(String(10), default="USD")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("mt5_accounts.id"), nullable=False)
    ticket = Column(String(50), unique=True, index=True)
    
    symbol = Column(String(20), nullable=False)
    type = Column(String(10), nullable=False)  # BUY, SELL
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    profit = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    commission = Column(Float, default=0.0)
    
    open_time = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("MT5Account", back_populates="positions")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("mt5_accounts.id"), nullable=False)
    ticket = Column(String(50), unique=True, index=True)
    
    symbol = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False)  # BUY_LIMIT, SELL_STOP, etc
    volume = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    
    time_setup = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    account = relationship("MT5Account", back_populates="orders")
