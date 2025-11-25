"""Direct MT5 connection test - bypasses the API"""
import MetaTrader5 as mt5
import subprocess
import time
import sys

print("=" * 50)
print("Direct MT5 Connection Test")
print("=" * 50)

# Account credentials
LOGIN = 99676234
PASSWORD = "Pk@11241008075"
SERVER = "XMGlobal-MT5 5"

MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

print(f"\nAccount: {LOGIN}")
print(f"Server: {SERVER}")
print("-" * 50)

# Check if MT5 is running, start if not
print("\n1. Checking MT5 terminal...")
try:
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Process terminal64 -ErrorAction SilentlyContinue'],
        capture_output=True, text=True, timeout=10
    )
    if 'terminal64' not in result.stdout:
        print("   Starting MT5 terminal...")
        subprocess.Popen([MT5_PATH], shell=False)
        time.sleep(5)
        print("   ✓ MT5 terminal started")
    else:
        print("   ✓ MT5 terminal already running")
except Exception as e:
    print(f"   Warning: Could not check MT5 status: {e}")

# Try to initialize and connect
print("\n2. Connecting to account...")
print(f"   Path: {MT5_PATH}")

# Shutdown any existing connection
mt5.shutdown()
time.sleep(1)

# Try approach 1: Initialize with credentials
if mt5.initialize(path=MT5_PATH, login=LOGIN, password=PASSWORD, server=SERVER, timeout=60000):
    print("   ✓ Connected successfully!")
    print(f"   Version: {mt5.version()}")
else:
    error1 = mt5.last_error()
    print(f"   First attempt failed: {error1}")
    
    # Try approach 2: Initialize then login
    mt5.shutdown()
    time.sleep(1)
    
    print("   Trying alternative approach...")
    if mt5.initialize(path=MT5_PATH):
        print("   MT5 initialized, attempting login...")
        if mt5.login(LOGIN, PASSWORD, SERVER, timeout=60000):
            print("   ✓ Connected successfully!")
            print(f"   Version: {mt5.version()}")
        else:
            error2 = mt5.last_error()
            print(f"   ✗ Login failed: {error2}")
            print("\n   The server may not be in MT5's server list.")
            print("   Please manually add the server in MT5 terminal first:")
            print(f"   1. Open MT5 → File → Login to Trade Account")
            print(f"   2. Enter login: {LOGIN}")
            print(f"   3. Enter server: {SERVER}")
            print("   4. This will add the server to MT5's list")
            sys.exit(1)
    else:
        print(f"   ✗ Failed to initialize MT5: {mt5.last_error()}")
        sys.exit(1)

# Get account info
print("\n3. Fetching account info...")
account_info = mt5.account_info()
if account_info:
    print(f"   Balance: {account_info.balance} {account_info.currency}")
    print(f"   Equity: {account_info.equity}")
    print(f"   Margin: {account_info.margin}")
    print(f"   Free Margin: {account_info.margin_free}")
    print(f"   Leverage: 1:{account_info.leverage}")
    print(f"   Server: {account_info.server}")
    print(f"   Company: {account_info.company}")

# Get positions
print("\n4. Checking open positions...")
positions = mt5.positions_get()
if positions:
    print(f"   Found {len(positions)} open position(s)")
    for pos in positions:
        print(f"   - {pos.symbol}: {pos.type} {pos.volume} lots @ {pos.price_open}, P/L: {pos.profit}")
else:
    print("   No open positions")

# Cleanup
mt5.shutdown()
print("\n" + "=" * 50)
print("Test completed successfully!")
print("=" * 50)
