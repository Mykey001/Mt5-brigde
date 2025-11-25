from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .config import settings
from .database import init_db
from .api import accounts, websocket
from .mt5.manager import mt5_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MT5 Bridge API",
    description="Bridge service for connecting multiple MT5 accounts to web application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting MT5 Bridge API...")
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize MT5
    if mt5_manager.initialize():
        logger.info("MT5 initialized successfully")
    else:
        logger.error("Failed to initialize MT5")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MT5 Bridge API...")
    mt5_manager.shutdown()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "MT5 Bridge API",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "mt5_initialized": mt5_manager._initialized,
        "active_connections": len(mt5_manager.active_connections)
    }
