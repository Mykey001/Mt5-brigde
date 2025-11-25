from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Security
    secret_key: str
    encryption_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis
    redis_url: str
    
    # MT5
    mt5_timeout: int = 60000
    mt5_path: str = r"C:\Program Files\MetaTrader 5\terminal64.exe"
    sync_interval_seconds: int = 2
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
