"""Test login with Vebson account"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Account credentials - JustMarkets Demo
account_data = {
    "user_id": 1,
    "broker_name": "JustMarkets",
    "account_number": "2001606102",
    "password": "Pk@11241008075",
    "server": "JustMarkets-Demo"
}

print("Testing MT5 account login...")
print(f"Account: {account_data['account_number']}")
print(f"Server: {account_data['server']}")
print(f"Broker: {account_data['broker_name']}")
print("-" * 50)

# First check if server is running
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    health = response.json()
    print(f"Server status: {health['status']}")
    print(f"MT5 initialized: {health['mt5_initialized']}")
except Exception as e:
    print(f"Server not running: {e}")
    exit(1)

# Try to create/login account
print("\nAttempting to connect account...")
print("(This may take up to 60 seconds...)")
try:
    response = requests.post(
        f"{BASE_URL}/api/accounts/",
        json=account_data,
        timeout=60
    )
    
    if response.status_code == 201:
        account = response.json()
        print("\n✓ SUCCESS! Account connected!")
        print(f"  Account ID: {account['id']}")
        print(f"  Status: {account['status']}")
        print(f"  Balance: {account['balance']} {account['currency']}")
        print(f"  Equity: {account['equity']}")
        print(f"  Leverage: 1:{account['leverage']}")
    elif response.status_code == 400:
        error = response.json()
        print(f"\n✗ Connection failed: {error.get('detail')}")
    elif response.status_code == 500:
        error = response.json()
        print(f"\n✗ Server error: {error.get('detail')}")
    else:
        print(f"\n✗ Unexpected response: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n✗ Error: {e}")
