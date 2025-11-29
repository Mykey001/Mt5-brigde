"""
Migration script to add account_name column to mt5_accounts table.
Run this script once to add the column to existing databases.

Usage: python add_account_name_column.py
"""
from sqlalchemy import create_engine, text, inspect
from app.config import settings

def migrate():
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('mt5_accounts')]
    
    if 'account_name' not in columns:
        with engine.connect() as conn:
            # Add the column (works for SQLite, PostgreSQL, MySQL)
            conn.execute(text("""
                ALTER TABLE mt5_accounts 
                ADD COLUMN account_name VARCHAR(200)
            """))
            conn.commit()
            print("✓ Added account_name column to mt5_accounts table")
    else:
        print("✓ account_name column already exists")

if __name__ == "__main__":
    migrate()
