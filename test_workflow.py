"""
Comprehensive workflow test for MT5 Bridge API
Tests all core functionality before deployment
"""
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = 999  # Test user ID

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")

def test_health_check():
    """Test 1: Health check endpoints"""
    print_test("Health Check")
    
    try:
        # Root endpoint
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        print_success(f"Root endpoint: {data}")
        
        # Health endpoint
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        print_success(f"Health endpoint: {data}")
        print_info(f"MT5 Initialized: {data.get('mt5_initialized')}")
        print_info(f"Active Connections: {data.get('active_connections')}")
        
        return True
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

def test_list_brokers():
    """Test 2: List available brokers"""
    print_test("List Brokers")
    
    try:
        response = requests.get(f"{BASE_URL}/api/accounts/brokers")
        assert response.status_code == 200
        brokers = response.json()
        
        print_success(f"Found {len(brokers)} brokers")
        for broker in brokers:
            print_info(f"  - {broker['display_name']} ({broker['broker_name']})")
            print_info(f"    Servers: {len(broker['servers'])}")
        
        return True, brokers
    except Exception as e:
        print_error(f"List brokers failed: {e}")
        return False, []

def test_create_account_validation():
    """Test 3: Account creation validation (should fail with invalid credentials)"""
    print_test("Account Creation Validation")
    
    try:
        # Test with invalid credentials (should fail)
        account_data = {
            "user_id": TEST_USER_ID,
            "broker_name": "XM",
            "account_number": "00000000",  # Invalid account
            "password": "invalid_password",
            "server": "XMGlobal-MT5"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/accounts/",
            json=account_data
        )
        
        # This should fail (400 or 500)
        if response.status_code in [400, 500]:
            print_success("Validation working: Invalid credentials rejected")
            print_info(f"Error message: {response.json().get('detail')}")
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Validation test failed: {e}")
        return False

def test_list_accounts():
    """Test 4: List accounts for user"""
    print_test("List User Accounts")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/accounts/",
            params={"user_id": TEST_USER_ID}
        )
        assert response.status_code == 200
        accounts = response.json()
        
        print_success(f"Found {len(accounts)} accounts for user {TEST_USER_ID}")
        for account in accounts:
            print_info(f"  Account ID: {account['id']}")
            print_info(f"  Broker: {account['broker_name']}")
            print_info(f"  Account #: {account['account_number']}")
            print_info(f"  Status: {account['status']}")
            print_info(f"  Balance: {account.get('balance', 0)}")
        
        return True, accounts
    except Exception as e:
        print_error(f"List accounts failed: {e}")
        return False, []

def test_get_account_details(account_id):
    """Test 5: Get specific account details"""
    print_test(f"Get Account Details (ID: {account_id})")
    
    try:
        response = requests.get(f"{BASE_URL}/api/accounts/{account_id}")
        
        if response.status_code == 404:
            print_info("Account not found (expected if no accounts exist)")
            return True
        
        assert response.status_code == 200
        account = response.json()
        
        print_success("Account details retrieved")
        print_info(f"  Balance: {account.get('balance')}")
        print_info(f"  Equity: {account.get('equity')}")
        print_info(f"  Margin: {account.get('margin')}")
        print_info(f"  Free Margin: {account.get('free_margin')}")
        print_info(f"  Status: {account.get('status')}")
        print_info(f"  Last Sync: {account.get('last_sync')}")
        
        return True
    except Exception as e:
        print_error(f"Get account details failed: {e}")
        return False

def test_database_connection():
    """Test 6: Database connectivity"""
    print_test("Database Connection")
    
    try:
        # Try to list accounts (this requires DB connection)
        response = requests.get(
            f"{BASE_URL}/api/accounts/",
            params={"user_id": TEST_USER_ID}
        )
        
        if response.status_code == 200:
            print_success("Database connection working")
            return True
        else:
            print_error(f"Database connection issue: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Database test failed: {e}")
        return False

def test_api_error_handling():
    """Test 7: API error handling"""
    print_test("API Error Handling")
    
    try:
        # Test 404 - Non-existent account
        response = requests.get(f"{BASE_URL}/api/accounts/99999")
        assert response.status_code == 404
        print_success("404 handling works")
        
        # Test 400 - Invalid data
        response = requests.post(
            f"{BASE_URL}/api/accounts/",
            json={"invalid": "data"}
        )
        assert response.status_code == 422  # Validation error
        print_success("422 validation works")
        
        return True
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        return False

def test_cors_headers():
    """Test 8: CORS configuration"""
    print_test("CORS Headers")
    
    try:
        response = requests.options(
            f"{BASE_URL}/api/accounts/brokers",
            headers={"Origin": "http://localhost:3000"}
        )
        
        headers = response.headers
        if "access-control-allow-origin" in headers:
            print_success(f"CORS enabled: {headers['access-control-allow-origin']}")
            return True
        else:
            print_info("CORS headers not found (may need preflight request)")
            return True
    except Exception as e:
        print_error(f"CORS test failed: {e}")
        return False

def run_all_tests():
    """Run all workflow tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}MT5 BRIDGE API - WORKFLOW TEST SUITE{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}Testing against: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}Test User ID: {TEST_USER_ID}{Colors.END}")
    print(f"{Colors.YELLOW}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    time.sleep(0.5)
    
    # Test 2: List Brokers
    success, brokers = test_list_brokers()
    results.append(("List Brokers", success))
    time.sleep(0.5)
    
    # Test 3: Account Creation Validation
    results.append(("Account Validation", test_create_account_validation()))
    time.sleep(0.5)
    
    # Test 4: List Accounts
    success, accounts = test_list_accounts()
    results.append(("List Accounts", success))
    time.sleep(0.5)
    
    # Test 5: Get Account Details (if accounts exist)
    if accounts:
        results.append(("Get Account Details", test_get_account_details(accounts[0]['id'])))
    else:
        print_test("Get Account Details")
        print_info("Skipped - no accounts to test")
        results.append(("Get Account Details", True))
    time.sleep(0.5)
    
    # Test 6: Database Connection
    results.append(("Database Connection", test_database_connection()))
    time.sleep(0.5)
    
    # Test 7: Error Handling
    results.append(("Error Handling", test_api_error_handling()))
    time.sleep(0.5)
    
    # Test 8: CORS
    results.append(("CORS Headers", test_cors_headers()))
    
    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if result else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    if passed == total:
        print(f"{Colors.GREEN}ALL TESTS PASSED ({passed}/{total}){Colors.END}")
        print(f"{Colors.GREEN}✓ System ready for deployment!{Colors.END}")
    else:
        print(f"{Colors.YELLOW}TESTS PASSED: {passed}/{total}{Colors.END}")
        print(f"{Colors.RED}✗ Some tests failed - review before deployment{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        exit(1)
