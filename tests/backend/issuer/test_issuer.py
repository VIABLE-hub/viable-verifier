#!/usr/bin/env python3
import requests
import json
import sys
import time
import base64
from urllib.parse import urlparse, parse_qs
from pprint import pprint

# Disable SSL warnings for testing
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://localhost:8080"
TEST_RESULTS = {
    "passed": 0,
    "failed": 0,
    "total": 0
}

def print_separator():
    print("=" * 80)

def run_test(name, test_func):
    print_separator()
    print(f"🧪 TEST: {name}")
    TEST_RESULTS["total"] += 1
    
    try:
        result = test_func()
        if result:
            print(f"✅ PASS: {name}")
            TEST_RESULTS["passed"] += 1
        else:
            print(f"❌ FAIL: {name}")
            TEST_RESULTS["failed"] += 1
    except Exception as e:
        print(f"❌ ERROR: {name} - {str(e)}")
        TEST_RESULTS["failed"] += 1
    
    print_separator()
    print()

def test_jwt_format():
    """Test the JWT format endpoint for iOS compatibility"""
    print("Testing JWT format for iOS compatibility...")
    url = f"{BASE_URL}/credential/test-jwt"
    response = requests.get(url, verify=False)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"JWT: {data.get('jwt', '')[:30]}...")
        
        # Check timestamp types
        timestamp_types = data.get('timestamp_types', {})
        print(f"Timestamp types: {timestamp_types}")
        
        # Verify all timestamps are floats
        all_floats = all(t == "float" for t in timestamp_types.values())
        print(f"All timestamps are floats: {all_floats}")
        
        return all_floats and response.status_code == 200
    else:
        print(f"Error: {response.text}")
        return False

def test_issuer_page_load():
    """Test that the issuer page loads correctly"""
    print("Testing issuer page load...")
    url = f"{BASE_URL}/issuer"
    response = requests.get(url, verify=False)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        # Check for key elements in the page
        key_elements = [
            "Studierendendaten",
            "Hochschul-Branding",
            "QR-Code",
            "fillRandomData",
            "form action"
        ]
        
        found_elements = []
        for element in key_elements:
            if element in response.text:
                found_elements.append(element)
                print(f"✓ Found '{element}'")
            else:
                print(f"✗ Missing '{element}'")
        
        return len(found_elements) == len(key_elements) and response.status_code == 200
    else:
        print(f"Error: {response.text}")
        return False

def test_credential_generation():
    """Test credential generation with mock data"""
    print("Testing credential generation with mock data...")
    
    # First, check if the debug endpoint is available
    debug_url = f"{BASE_URL}/credential/debug"
    response = requests.get(debug_url, verify=False)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Credential format: {data.get('format', '')}")
        print(f"JWT length: {len(data.get('credential', ''))}")
        
        # Verify credential structure
        credential = data.get('credential', '')
        parts = credential.split('.')
        valid_structure = len(parts) == 3
        print(f"Valid JWT structure (3 parts): {valid_structure}")
        
        if valid_structure:
            # Decode payload
            payload_part = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
            try:
                payload = json.loads(base64.urlsafe_b64decode(payload_part).decode('utf-8'))
                
                # Check for required fields
                required_fields = ["iat", "exp", "nbf", "vc"]
                missing_fields = [field for field in required_fields if field not in payload]
                
                if missing_fields:
                    print(f"Missing required fields: {missing_fields}")
                    return False
                else:
                    print("All required fields present in payload")
                    
                    # Check timestamp types
                    timestamp_fields = ["iat", "exp", "nbf"]
                    timestamp_types = {field: type(payload[field]).__name__ for field in timestamp_fields}
                    print(f"Timestamp types: {timestamp_types}")
                    
                    # Verify all timestamps are floats
                    all_floats = all(t == "float" for t in timestamp_types.values())
                    print(f"All timestamps are floats: {all_floats}")
                    
                    return all_floats
            except Exception as e:
                print(f"Error decoding payload: {str(e)}")
                return False
        
        return valid_structure
    else:
        print(f"Debug endpoint not available. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_credential_signing():
    """Test BBS+ credential signing"""
    print("Testing BBS+ credential signing...")
    
    # Use the debug endpoint to test signing
    debug_url = f"{BASE_URL}/credential/debug"
    response = requests.get(debug_url, verify=False)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if signature is present
        signature = data.get('signature', '')
        if not signature:
            print("No signature found in response")
            return False
        
        print(f"Signature length: {len(signature)}")
        print(f"Signature starts with: {signature[:30]}...")
        
        # Basic validation - just check that we got a non-empty string
        return bool(signature)
    else:
        print(f"Debug endpoint not available. Status code: {response.status_code}")
        print(f"Error: {response.text}")
        return False

def test_initialize_keys():
    """Test key initialization"""
    print("Testing key initialization...")
    
    # Use the test-jwt endpoint which initializes keys
    url = f"{BASE_URL}/credential/test-jwt"
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        data = response.json()
        
        # Check header for key ID
        header = data.get('header', {})
        kid = header.get('kid', '')
        
        print(f"Key ID: {kid}")
        return bool(kid)
    else:
        print(f"Error: {response.text}")
        return False

def test_issuer_form_submission():
    """Test form submission to the issuer endpoint"""
    print("\n🧪 Testing issuer form submission...")
    url = f"{BASE_URL}/issuer"
    form_data = {
        "firstName": "TestUser",
        "lastName": "TestLastName",
        "studentId": "123456",
        "studentIdPrefix": "TU",
        "theme_bgColorCard": "003f7f",
        "theme_fgColorTitle": "FFFFFF",
        "theme_accentColor": "E6007E",
        "theme_textColor": "333333"
    }
    
    response = requests.post(url, data=form_data, verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response contains QR code: {'img_data' in response.text}")
    print(f"Response contains credential offer URI: {'openid-credential-offer://' in response.text}")
    
    return "openid-credential-offer://" in response.text

def test_credential_offer_flow():
    """Test the credential offer endpoint"""
    print("\n🧪 Testing credential offer flow...")
    
    # 1. Submit form to get credential offer
    url = f"{BASE_URL}/issuer"
    form_data = {
        "firstName": "TestUser",
        "lastName": "TestLastName",
        "studentId": "123456",
        "studentIdPrefix": "TU",
        "theme_bgColorCard": "003f7f",
        "theme_fgColorTitle": "FFFFFF" 
    }
    
    response = requests.post(url, data=form_data, verify=False)
    
    # Find the credential offer URI in the response
    import re
    match = re.search(r'openid-credential-offer://\?credential_offer_uri=([^"]+)', response.text)
    if not match:
        print("❌ Failed to find credential offer URI in response")
        return False
    
    credential_offer_uri = match.group(1)
    print(f"Found credential offer URI: {credential_offer_uri}")
    
    # 2. Call credential offer endpoint
    offer_response = requests.get(credential_offer_uri, verify=False)
    print(f"Credential offer status code: {offer_response.status_code}")
    
    if offer_response.status_code != 200:
        print("❌ Failed to get credential offer")
        return False
    
    try:
        offer_data = offer_response.json()
        print("📄 Credential offer response:")
        pprint(offer_data)
        return "credential_issuer" in offer_data and "grants" in offer_data
    except Exception as e:
        print(f"❌ Failed to parse credential offer JSON: {e}")
        return False

def extract_token_from_url(url):
    """Extract the token from a URL parameter"""
    # Format: https://example.com/redirect?token=abcdef
    if "?" not in url:
        return None
    params = url.split("?", 1)[1].split("&")
    for param in params:
        if param.startswith("token="):
            return param.split("=", 1)[1]
    return None

def run_all_tests():
    """Run all issuer tests"""
    print("🚀 Running all issuer tests...\n")
    
    # Basic functionality tests
    run_test("Issuer Page Load", test_issuer_page_load)
    run_test("JWT Format for iOS", test_jwt_format)
    run_test("Key Initialization", test_initialize_keys)
    run_test("Credential Generation", test_credential_generation)
    run_test("BBS+ Credential Signing", test_credential_signing)
    
    # Additional tests
    run_test("Issuer Form Submission", test_issuer_form_submission)
    run_test("Credential Offer Flow", test_credential_offer_flow)
    
    # Print summary
    print(f"📊 TEST SUMMARY: {TEST_RESULTS['passed']}/{TEST_RESULTS['total']} tests passed")
    print(f"✅ Passed: {TEST_RESULTS['passed']}")
    print(f"❌ Failed: {TEST_RESULTS['failed']}")
    
    return TEST_RESULTS["failed"] == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 