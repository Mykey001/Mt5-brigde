from celery import Celery
from sqlalchemy.orm import Session
import logging
from ..config import settings
from ..database import SessionLocal
from ..models import MT5Account, ConnectionStatus
from ..mt5.sync import sync_service

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "mt5_bridge",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sync-all-accounts": {
            "task": "app.workers.sync_worker.sync_all_accounts",
            "schedule": settings.sync_interval_seconds,
        },
    },
)

@celery_app.task
def sync_all_accounts():
    """Background task to sync all connected accounts"""
    db = SessionLocal()
    try:
        accounts = db.query(MT5Account).filter(
            MT5Account.status == ConnectionStatus.CONNECTED
        ).all()
        
        for account in accounts:
            try:
                sync_service.sync_account(account, db)
            except Exception as e:
                logger.error(f"Error syncing account {account.id}: {e}")
        
        logger.info(f"Synced {len(accounts)} accounts")
        
    finally:
        db.close()

@celery_app.task
def sync_single_account(account_id: int):
    """Sync a single account"""
    db = SessionLocal()
    try:
        account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
        if account:
            sync_service.sync_account(account, db)
            logger.info(f"Synced account {account_id}")
    finally:
        db.close()
