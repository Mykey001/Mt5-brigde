from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import MT5Account, ConnectionStatus
from ..schemas import AccountCreate, AccountResponse, AccountUpdate, BrokerInfo
from ..security import encrypt_credentials, decrypt_credentials
from ..mt5.manager import mt5_manager
from ..mt5.sync import sync_service
from ..mt5.brokers import get_all_brokers, get_broker_servers

router = APIRouter(prefix="/accounts", tags=["accounts"])

@router.get("/brokers", response_model=List[BrokerInfo])
async def list_brokers():
    """Get list of available brokers and their servers"""
    return get_all_brokers()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create and connect new MT5 account
    Flow:
    1. Validate credentials
    2. Encrypt password
    3. Attempt MT5 connection
    4. Save to database
    5. Perform initial sync
    """
    # Check if account already exists
    existing = db.query(MT5Account).filter(
        MT5Account.user_id == account_data.user_id,
        MT5Account.account_number == account_data.account_number,
        MT5Account.broker_name == account_data.broker_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already exists"
        )
    
    # Encrypt password
    encrypted_password = encrypt_credentials(account_data.password)
    
    # Create account record
    account = MT5Account(
        user_id=account_data.user_id,
        broker_name=account_data.broker_name,
        account_number=account_data.account_number,
        encrypted_password=encrypted_password,
        server=account_data.server,
        status=ConnectionStatus.CONNECTING
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Attempt connection and initial sync
    try:
        success = sync_service.sync_account(account, db)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to connect: {account.error_message}"
            )
    except Exception as e:
        db.delete(account)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection error: {str(e)}"
        )
    
    return account

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all accounts for a user"""
    accounts = db.query(MT5Account).filter(
        MT5Account.user_id == user_id
    ).all()
    return accounts

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get specific account details"""
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db)
):
    """Update account credentials or server"""
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Update fields
    if account_data.password:
        account.encrypted_password = encrypt_credentials(account_data.password)
    if account_data.server:
        account.server = account_data.server
    
    # Reconnect with new credentials
    account.status = ConnectionStatus.CONNECTING
    db.commit()
    
    success = sync_service.sync_account(account, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to reconnect: {account.error_message}"
        )
    
    return account

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Delete account and disconnect"""
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Disconnect from MT5
    mt5_manager.disconnect_account(account_id)
    
    # Delete from database (cascade will remove positions/orders)
    db.delete(account)
    db.commit()

@router.post("/{account_id}/reconnect", response_model=AccountResponse)
async def reconnect_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Manually reconnect account"""
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    account.status = ConnectionStatus.CONNECTING
    db.commit()
    
    success = sync_service.sync_account(account, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reconnection failed: {account.error_message}"
        )
    
    return account

@router.post("/{account_id}/sync")
async def force_sync(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Force immediate sync for account"""
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    success = sync_service.sync_account(account, db)
    return {"success": success, "last_sync": account.last_sync}


@router.get("/{account_id}/deals")
async def get_account_deals(
    account_id: int,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get deal history for an account
    Always syncs the account first to ensure we're connected to the correct account
    """
    from ..mt5.history import get_deals_history
    
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # ALWAYS sync to ensure we're connected to THIS specific account
    # (another account may have been connected in between)
    success = sync_service.sync_account(account, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect: {account.error_message}"
        )
    
    # Get deals from the now-connected account
    deals = get_deals_history(days)
    
    return {
        "account_id": account_id,
        "account_number": account.account_number,
        "days": days,
        "count": len(deals),
        "deals": deals
    }


@router.get("/{account_id}/orders-history")
async def get_account_orders_history(
    account_id: int,
    days: int = 90,
    db: Session = Depends(get_db)
):
    """
    Get order history for an account
    Always syncs the account first to ensure we're connected to the correct account
    """
    from ..mt5.history import get_orders_history
    
    account = db.query(MT5Account).filter(MT5Account.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # ALWAYS sync to ensure we're connected to THIS specific account
    success = sync_service.sync_account(account, db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to connect: {account.error_message}"
        )
    
    # Get orders from the now-connected account
    orders = get_orders_history(days)
    
    return {
        "account_id": account_id,
        "account_number": account.account_number,
        "days": days,
        "count": len(orders),
        "orders": orders
    }


from pydantic import BaseModel

class MigrateRequest(BaseModel):
    from_user_id: int
    to_user_id: int

@router.post("/migrate")
async def migrate_accounts(
    request: MigrateRequest,
    db: Session = Depends(get_db)
):
    """
    Migrate accounts from one user_id to another
    Used when the web app's user ID format changes
    """
    # Find accounts belonging to the old user_id
    accounts = db.query(MT5Account).filter(
        MT5Account.user_id == request.from_user_id
    ).all()
    
    if not accounts:
        return {
            "success": True,
            "migratedCount": 0,
            "message": f"No accounts found for user_id {request.from_user_id}"
        }
    
    # Update user_id for all found accounts
    migrated_count = 0
    for account in accounts:
        account.user_id = request.to_user_id
        migrated_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "migratedCount": migrated_count,
        "message": f"Migrated {migrated_count} accounts from user {request.from_user_id} to {request.to_user_id}"
    }
