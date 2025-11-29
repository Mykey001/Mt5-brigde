from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models import Base

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    
    # Run migrations for existing databases
    _run_migrations()

def _run_migrations():
    """Run any pending migrations for existing databases"""
    from sqlalchemy import inspect, text
    import logging
    
    logger = logging.getLogger(__name__)
    inspector = inspect(engine)
    
    # Check if mt5_accounts table exists
    if 'mt5_accounts' not in inspector.get_table_names():
        logger.info("mt5_accounts table doesn't exist yet, will be created by create_all")
        return
    
    # Check if account_name column exists
    columns = [col['name'] for col in inspector.get_columns('mt5_accounts')]
    
    if 'account_name' not in columns:
        logger.info("Adding account_name column to mt5_accounts table...")
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE mt5_accounts ADD COLUMN account_name VARCHAR(200)"))
                conn.commit()
            logger.info("Successfully added account_name column")
        except Exception as e:
            logger.error(f"Failed to add account_name column: {e}")
    else:
        logger.info("account_name column already exists")
