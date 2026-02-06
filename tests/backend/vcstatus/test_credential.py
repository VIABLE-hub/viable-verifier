#!/usr/bin/env python3
import requests
import json
import sys

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings()

# Test the debug endpoint
def test_credential_debug():
    print("Testing credential debug endpoint...")
    url = "https://localhost:8080/credential/debug"
    response = requests.get(url, verify=False)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Credential generated successfully.")
        data = response.json()
        print(f"Format: {data.get('format')}")
        print(f"JWT length: {len(data.get('credential', ''))}")
        print(f"Signature length: {len(data.get('signature', ''))}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

# Test the JWT format test endpoint
def test_jwt_format():
    print("\nTesting JWT format endpoint...")
    url = "https://localhost:8080/credential/test-jwt"
    response = requests.get(url, verify=False)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Success! JWT format test passed.")
        data = response.json()
        print(f"Timestamp types: {data.get('timestamp_types')}")
        print(f"Validation: {data.get('validation')}")
        print(f"JWT structure: {data.get('jwt_structure')}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

if __name__ == "__main__":
    success = True
    
    # Test JWT format first
    if not test_jwt_format():
        success = False
    
    # Test credential debug endpoint
    if not test_credential_debug():
        success = False
    
    if success:
        print("\n✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1) 