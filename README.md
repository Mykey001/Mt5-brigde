# MT5 Bridge API

Python bridge service that connects multiple MT5 accounts (XM, Exness, JustMarkets, etc.) to your web application.

## ⚠️ Important: Windows Only

**The MT5 Python library only works on Windows.** This application must run on a Windows machine where MetaTrader 5 terminal is installed.

## Features

- **Multi-Account Management**: Connect multiple broker accounts (XM, Exness, JustMarkets, IC Markets, etc.)
- **Secure Credential Storage**: Encrypted password storage using Fernet encryption
- **Real-time Data Sync**: WebSocket-based live updates
- **Auto-Reconnect**: Automatic reconnection on disconnections
- **REST API**: Full CRUD operations for account management
- **No Manual MT5 Login Required**: Connect accounts directly via API (for known servers)

## Architecture

```
Web App → REST API → Python Bridge → MT5 Terminal
                ↓
            Database (PostgreSQL)
                ↓
         WebSocket Updates → Web App
```

## Quick Start (Windows)

### Prerequisites

- Windows 10/11 or Windows Server
- Python 3.10+
- MetaTrader 5 Terminal installed
- Docker Desktop (optional, for PostgreSQL/Redis)

### 1. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Start Database Services (Docker)

```powershell
docker-compose up -d
```

This starts PostgreSQL and Redis containers.

### 3. Configure Environment

```powershell
copy .env.example .env
# Edit .env with your settings
```

### 4. Run the API

```powershell
# Option 1: Using the deployment script
.\deploy_windows.ps1

# Option 2: Manual
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Test the API

```powershell
python test_workflow.py
```

## API Endpoints

### Health Check

- **GET** `/` - Basic health check
- **GET** `/health` - Detailed health status

### Brokers

- **GET** `/api/accounts/brokers` - List available brokers and servers

### Accounts

- **POST** `/api/accounts/` - Create and connect MT5 account
- **GET** `/api/accounts/?user_id={id}` - List user's accounts
- **GET** `/api/accounts/{account_id}` - Get account details
- **PUT** `/api/accounts/{account_id}` - Update account
- **DELETE** `/api/accounts/{account_id}` - Delete account
- **POST** `/api/accounts/{account_id}/reconnect` - Reconnect account
- **POST** `/api/accounts/{account_id}/sync` - Force sync

### WebSocket

- **WS** `/api/ws/{user_id}` - Real-time updates

## Usage Example

### Connect an Account

```javascript
const response = await fetch('http://localhost:8000/api/accounts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 1,
    broker_name: 'JustMarkets',
    account_number: '2001606102',
    password: 'your_password',
    server: 'JustMarkets-Demo'
  })
});

const account = await response.json();
// { id: 1, status: 'connected', balance: 203.19, ... }
```

### WebSocket Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/1');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'account_update') {
    console.log('Balance:', message.data.balance);
    console.log('Positions:', message.data.positions);
  }
};
```

## Configuration

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://mt5bridge:mt5bridge_password@localhost:5432/mt5bridge

# Security - CHANGE IN PRODUCTION!
SECRET_KEY=your-secret-key-change-this
ENCRYPTION_KEY=your-encryption-key-change-this

# Redis
REDIS_URL=redis://localhost:6379/0

# MT5
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_TIMEOUT=60000

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## Adding New Brokers

Edit `app/mt5/brokers.py`:

```python
BROKER_CONFIGS = {
    "YourBroker": {
        "name": "Your Broker Display Name",
        "servers": [
            {"name": "YourBroker-Server", "description": "Main Server"},
        ]
    },
}
```

## Server Requirements

For a new broker server to work:
1. The server must be added to MT5 terminal's server list at least once
2. This can be done by manually logging in via MT5 terminal once
3. After that, the API can connect automatically

## Deployment

### Windows Server Deployment

1. Install Python 3.10+ and MT5 Terminal
2. Clone the repository
3. Run `deploy_windows.ps1`
4. Set up as Windows Service (optional):
   ```powershell
   # Use NSSM or similar to run as service
   nssm install MT5Bridge "C:\Python313\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
   ```

### Docker (Database Only)

The `docker-compose.yml` runs PostgreSQL and Redis. The API must run on Windows.

```powershell
# Start database services
docker-compose up -d

# Run API on Windows
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### "Authorization failed" Error
- MT5 terminal must be running
- Enable "Allow Algo Trading" in MT5 (Tools → Options → Expert Advisors)
- For new servers, login manually in MT5 once to add the server

### "IPC timeout" Error
- Restart MT5 terminal
- Check if MT5 path is correct in .env
- Ensure Python and MT5 are both 64-bit

### Connection Issues
- Verify account credentials
- Check server name matches exactly (case-sensitive)
- Ensure MT5 terminal has the broker's server in its list

## License

MIT
