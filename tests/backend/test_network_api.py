#!/usr/bin/env python3
import requests
import time
import urllib3
import json
import sys

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base URL for the API
BASE_URL = "https://localhost:8080"

# Network API endpoints to test
endpoints = [
    f"{BASE_URL}/api/system/network",
    f"{BASE_URL}/api/system/network/refresh",
    f"{BASE_URL}/settings/api/network-info"
]

def test_endpoint(url):
    """Test a single endpoint and return the status code and response data"""
    try:
        print(f"Testing endpoint: {url}")
        response = requests.get(url, verify=False, timeout=10)
        status = response.status_code
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status}")
            print(f"Response data: {json.dumps(data, indent=2)}")
            return status, data
        except ValueError:
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status} (Not JSON)")
            print(f"Response text: {response.text[:200]}...")  # Show first 200 chars
            return status, response.text
            
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - {url} - Error: {e}")
        return -1, str(e)

def test_all_endpoints():
    """Test all network API endpoints and return results"""
    print(f"--- Testing network endpoints at {time.strftime('%H:%M:%S')} ---")
    results = []
    
    for endpoint in endpoints:
        status, data = test_endpoint(endpoint)
        results.append({
            "endpoint": endpoint,
            "status": status,
            "data": data
        })
        print("-" * 50)
    
    print(f"--- Completed testing at {time.strftime('%H:%M:%S')} ---")
    
    # Count successful tests
    success_count = sum(1 for r in results if r["status"] == 200)
    print(f"Successful tests: {success_count}/{len(endpoints)}")
    
    return results

def test_ngrok_config():
    """Test the NGROK configuration endpoint"""
    url = f"{BASE_URL}/api/system/network/ngrok"
    
    # Sample NGROK configuration data
    ngrok_data = {
        "ngrok_url": "https://example-test.ngrok-free.app",
        "use_for_issuer": True,
        "use_for_verifier": True
    }
    
    try:
        print(f"Testing NGROK configuration at {url}")
        response = requests.post(
            url, 
            json=ngrok_data,
            verify=False, 
            timeout=10
        )
        status = response.status_code
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status}")
            print(f"Response data: {json.dumps(data, indent=2)}")
            return status, data
        except ValueError:
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status} (Not JSON)")
            print(f"Response text: {response.text[:200]}...")  # Show first 200 chars
            return status, response.text
            
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - {url} - Error: {e}")
        return -1, str(e)

def test_network_diagnostics():
    """Test the network diagnostics endpoint"""
    url = f"{BASE_URL}/api/system/network/test"
    
    try:
        print(f"Testing network diagnostics at {url}")
        response = requests.post(url, verify=False, timeout=20)  # Longer timeout for diagnostics
        status = response.status_code
        
        # Try to parse JSON response
        try:
            data = response.json()
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status}")
            print(f"Response data: {json.dumps(data, indent=2)}")
            return status, data
        except ValueError:
            print(f"{time.strftime('%H:%M:%S')} - {url} - Status: {status} (Not JSON)")
            print(f"Response text: {response.text[:200]}...")  # Show first 200 chars
            return status, response.text
            
    except Exception as e:
        print(f"{time.strftime('%H:%M:%S')} - {url} - Error: {e}")
        return -1, str(e)

if __name__ == "__main__":
    print("Starting network API tests...")
    
    # Test basic endpoints
    results = test_all_endpoints()
    
    # Only continue with additional tests if basic endpoints are working
    if any(r["status"] == 200 for r in results):
        print("\nTesting NGROK configuration...")
        test_ngrok_config()
        
        print("\nTesting network diagnostics...")
        test_network_diagnostics()
    
    print("\nAll tests completed!") 