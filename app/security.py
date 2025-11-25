from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from .config import settings
import base64
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_encryption_key() -> bytes:
    """Generate consistent encryption key from settings"""
    key = hashlib.sha256(settings.encryption_key.encode()).digest()
    return base64.urlsafe_b64encode(key)

cipher = Fernet(get_encryption_key())

def encrypt_credentials(password: str) -> str:
    """Encrypt MT5 password"""
    return cipher.encrypt(password.encode()).decode()

def decrypt_credentials(encrypted_password: str) -> str:
    """Decrypt MT5 password"""
    return cipher.decrypt(encrypted_password.encode()).decode()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
