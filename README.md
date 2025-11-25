# MT5 Bridge API

Python bridge service that connects multiple MT5 accounts (XM, Exness, etc.) to your web application without requiring direct MT5 login.

## Features

- **Multi-Account Management**: Connect multiple broker accounts (XM, Exness, IC Markets, etc.)
- **Secure Credential Storage**: Encrypted password storage using Fernet encryption
- **Real-time Data Sync**: WebSocket-based live updates every 2 seconds
- **Auto-Reconnect**: Automatic reconnection on disconnections
- **REST API**: Full CRUD operations for account management
- **Background Workers**: Celery-based periodic sync workers

## Architecture

```
Web App → REST API → Python Bridge → MT5 Terminal
                ↓
            Database (PostgreSQL)
                ↓
         WebSocket Updates → Web App
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis (for Celery)
- MetaTrader 5 Terminal installed on Windows

### Setup

1. **Clone and install dependencies**:
```bash
cd mt5-bridge
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Initialize database**:
```bash
# Database will auto-initialize on first run
# Or manually with alembic:
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

4. **Start services**:

Terminal 1 - API Server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Celery Worker:
```bash
celery -A app.workers.sync_worker worker --loglevel=info
```

Terminal 3 - Celery Beat (scheduler):
```bash
celery -A app.workers.sync_worker beat --loglevel=info
```

## API Endpoints

### Brokers

**GET** `/api/accounts/brokers`
- Get list of available brokers and their servers

### Accounts

**POST** `/api/accounts/`
- Create and connect new MT5 account
- Body: `{user_id, broker_name, account_number, password, server}`

**GET** `/api/accounts/?user_id={user_id}`
- List all accounts for a user

**GET** `/api/accounts/{account_id}`
- Get specific account details

**PUT** `/api/accounts/{account_id}`
- Update account credentials/server

**DELETE** `/api/accounts/{account_id}`
- Delete account and disconnect

**POST** `/api/accounts/{account_id}/reconnect`
- Manually reconnect account

**POST** `/api/accounts/{account_id}/sync`
- Force immediate sync

### WebSocket

**WS** `/api/ws/{user_id}`
- Real-time updates for all user accounts
- Receives: account balance, positions, orders updates

## Usage Example

### 1. Connect Account (Web App → API)

```javascript
// Frontend code
const response = await fetch('http://localhost:8000/api/accounts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 123,
    broker_name: 'XM',
    account_number: '12345678',
    password: 'your_password',
    server: 'XMGlobal-MT5'
  })
});

const account = await response.json();
console.log('Connected:', account);
```

### 2. WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/123');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'account_update') {
    console.log('Account update:', message.data);
    // Update UI with new balance, positions, etc.
  }
};

// Keep alive
setInterval(() => {
  ws.send(JSON.stringify({ type: 'ping' }));
}, 30000);
```

### 3. Get Available Servers

```javascript
const brokers = await fetch('http://localhost:8000/api/accounts/brokers')
  .then(r => r.json());

// Display broker/server selection UI
brokers.forEach(broker => {
  console.log(broker.broker_name, broker.servers);
});
```

## Data Flow

### Account Connection Flow
1. Web app sends credentials to `/api/accounts/`
2. Bridge encrypts password with Fernet
3. Bridge connects to MT5 with specified server
4. On success, performs initial sync (account info, positions, orders)
5. Saves to database
6. Returns account details to web app
7. WebSocket pushes initial data

### Periodic Sync (Every 2 seconds)
1. Celery Beat triggers `sync_all_accounts` task
2. Worker queries all connected accounts
3. For each account:
   - Reconnect to MT5
   - Fetch account info, positions, orders
   - Update database
   - Push updates via WebSocket

### Auto-Reconnect
- On connection failure, marks account as ERROR
- Next sync attempt will retry connection
- Configurable max retry attempts

## Security

- **Encryption**: Passwords encrypted with Fernet (AES-128)
- **JWT Auth**: Token-based authentication (implement in production)
- **CORS**: Configurable allowed origins
- **Environment Variables**: Sensitive data in .env

## Configuration

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mt5bridge

# Security - CHANGE THESE!
SECRET_KEY=generate-random-secret-key
ENCRYPTION_KEY=generate-random-encryption-key

# Sync Settings
SYNC_INTERVAL_SECONDS=2
AUTO_RECONNECT=true
MAX_RECONNECT_ATTEMPTS=5

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Adding More Brokers

Edit `app/mt5/brokers.py`:

```python
BROKER_CONFIGS = {
    "YourBroker": {
        "name": "Your Broker Name",
        "servers": [
            {"name": "YourBroker-MT5", "description": "Main Server"},
            {"name": "YourBroker-MT5-2", "description": "Server 2"},
        ]
    },
}
```

## Troubleshooting

**MT5 won't connect**:
- Ensure MT5 terminal is installed
- Check server name matches exactly
- Verify credentials
- Check firewall settings

**WebSocket disconnects**:
- Implement ping/pong keep-alive (included)
- Check network stability
- Increase timeout settings

**Sync delays**:
- Adjust `SYNC_INTERVAL_SECONDS` in .env
- Check Redis connection
- Monitor Celery worker logs

## Production Deployment

1. Use production WSGI server (Gunicorn)
2. Set up reverse proxy (Nginx)
3. Use managed PostgreSQL/Redis
4. Implement proper JWT authentication
5. Enable HTTPS for WebSocket (WSS)
6. Set up monitoring (Sentry, Prometheus)
7. Use environment-specific configs

## License

MIT
# Mt5-brigde
