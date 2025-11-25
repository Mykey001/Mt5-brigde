"""
Helper script to add a new broker server to MT5 terminal.

MT5 Python API cannot add servers programmatically.
You need to add the server manually in MT5 terminal ONCE,
then the API can connect to it automatically.

Steps:
1. Open MT5 Terminal
2. Go to File → Login to Trade Account (or press Ctrl+L)
3. In the login dialog, enter:
   - Login: 2050587391
   - Password: Edward@6416
   - Server: JustMarkets-Live
4. Click "Login"
5. If the server is not in the list, click "Add new broker"
   and search for "JustMarkets" or enter the server address

After doing this once, the server will be saved in MT5's server list
and the API will be able to connect automatically.
"""

import subprocess
import os

MT5_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"

print("=" * 60)
print("MT5 Server Setup Helper")
print("=" * 60)
print()
print("To connect to a new broker server, you need to add it to")
print("MT5 terminal's server list first (one-time setup).")
print()
print("Opening MT5 terminal...")

try:
    subprocess.Popen([MT5_PATH], shell=False)
    print("✓ MT5 terminal opened")
    print()
    print("Please follow these steps in MT5:")
    print("-" * 60)
    print("1. Press Ctrl+L (or File → Login to Trade Account)")
    print("2. Enter the following credentials:")
    print("   Login:    2050587391")
    print("   Password: Edward@6416")
    print("   Server:   JustMarkets-Live")
    print("3. If server not found, click 'Add new broker'")
    print("   and search for 'JustMarkets'")
    print("4. Click 'Login'")
    print("-" * 60)
    print()
    print("After successful login, run test_mt5_direct.py again.")
except Exception as e:
    print(f"✗ Could not open MT5: {e}")
    print(f"  Please open manually: {MT5_PATH}")
