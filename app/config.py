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
    mt5_path: Optional[str] = None  # Will auto-detect if not set
    sync_interval_seconds: int = 2
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    
    def get_mt5_path(self) -> str:
        """Get MT5 path, auto-detecting if not configured"""
        if self.mt5_path:
            return self.mt5_path
        
        import os
        # Common MT5 installation paths
        common_paths = [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
            os.path.expanduser(r"~\AppData\Roaming\MetaQuotes\Terminal\*\terminal64.exe"),
        ]
        
        for path in common_paths:
            if '*' in path:
                import glob
                matches = glob.glob(path)
                if matches:
                    return matches[0]
            elif os.path.exists(path):
                return path
        
        # Default fallback
        return r"C:\Program Files\MetaTrader 5\terminal64.exe"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
