#!/usr/bin/env python3
"""
Test script to simulate verifier endpoint calls and test selective disclosure
"""

import requests
import json
import urllib.parse

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

BASE_URL = "https://localhost:8080"

def test_verifier_presentation_request_working_style():
    """Test verifier with working version style (technical fields only)"""
    print("🧪 TESTING WORKING VERSION STYLE (Technical Fields Only)")
    print("=" * 60)
    
    # Simulate the verifier form submission with NO user fields selected
    url = f"{BASE_URL}/verifier"
    
    # Post with only technical fields (like working version)
    form_data = {
        # Don't select any user fields - this simulates working version behavior
    }
    
    try:
        response = requests.post(url, data=form_data, verify=False, allow_redirects=False)
        print(f"Verifier form submission status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Verifier page loaded successfully")
            
            # Now test the presentation-request endpoint
            presentation_url = f"{BASE_URL}/verifier/presentation-request"
            response = requests.get(presentation_url, verify=False, allow_redirects=False)
            
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"✅ Presentation request created: {response.status_code}")
                print(f"Redirect URL length: {len(redirect_url)}")
                
                # Extract and decode the presentation definition
                if 'presentation_definition=' in redirect_url:
                    # Find the presentation_definition parameter
                    parts = redirect_url.split('presentation_definition=')
                    if len(parts) > 1:
                        encoded_def = parts[1].split('&')[0]  # Get until next parameter
                        try:
                            # URL decode and parse JSON
                            decoded_def = urllib.parse.unquote_plus(encoded_def)
                            presentation_def = json.loads(decoded_def)
                            
                            print(f"\n📋 Presentation Definition (Working Style):")
                            print(json.dumps(presentation_def, indent=2))
                            
                            mandatory_fields = presentation_def.get('mandatory_fields', [])
                            print(f"\n📊 Field Analysis:")
                            print(f"   Total mandatory fields: {len(mandatory_fields)}")
                            
                            # Check for user fields
                            user_fields = [f for f in mandatory_fields if 'credentialSubject' in f or f in ['firstName', 'lastName', 'studentId']]
                            technical_fields = [f for f in mandatory_fields if f not in user_fields]
                            
                            print(f"   Technical fields: {len(technical_fields)}")
                            print(f"   User fields: {len(user_fields)}")
                            
                            if user_fields:
                                print(f"   ❌ Contains user fields: {user_fields}")
                                print(f"   This explains why verification fails!")
                            else:
                                print(f"   ✅ Only technical fields - should work!")
                                
                        except Exception as e:
                            print(f"❌ Failed to decode presentation definition: {e}")
                else:
                    print("❌ No presentation_definition found in redirect URL")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
        else:
            print(f"❌ Verifier form submission failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing working style: {e}")

def test_verifier_presentation_request_current_style():
    """Test verifier with current style (technical + user fields)"""
    print("\n🧪 TESTING CURRENT STYLE (Technical + User Fields)")
    print("=" * 60)
    
    # Simulate the verifier form submission WITH user fields selected
    url = f"{BASE_URL}/verifier"
    
    # Post with lastName selected (this causes the failure)
    form_data = {
        'lastName': 'on'  # This simulates selecting lastName checkbox
    }
    
    try:
        response = requests.post(url, data=form_data, verify=False, allow_redirects=False)
        print(f"Verifier form submission status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Verifier page loaded successfully")
            
            # Now test the presentation-request endpoint  
            presentation_url = f"{BASE_URL}/verifier/presentation-request"
            response = requests.get(presentation_url, verify=False, allow_redirects=False)
            
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"✅ Presentation request created: {response.status_code}")
                print(f"Redirect URL length: {len(redirect_url)}")
                
                # Extract and decode the presentation definition
                if 'presentation_definition=' in redirect_url:
                    parts = redirect_url.split('presentation_definition=')
                    if len(parts) > 1:
                        encoded_def = parts[1].split('&')[0]
                        try:
                            decoded_def = urllib.parse.unquote_plus(encoded_def)
                            presentation_def = json.loads(decoded_def)
                            
                            print(f"\n📋 Presentation Definition (Current Style):")
                            print(json.dumps(presentation_def, indent=2))
                            
                            mandatory_fields = presentation_def.get('mandatory_fields', [])
                            print(f"\n📊 Field Analysis:")
                            print(f"   Total mandatory fields: {len(mandatory_fields)}")
                            
                            # Check for user fields
                            user_fields = [f for f in mandatory_fields if 'credentialSubject' in f or f in ['firstName', 'lastName', 'studentId']]
                            technical_fields = [f for f in mandatory_fields if f not in user_fields]
                            
                            print(f"   Technical fields: {len(technical_fields)}")
                            print(f"   User fields: {len(user_fields)}")
                            
                            if user_fields:
                                print(f"   ❌ Contains user fields: {user_fields}")
                                print(f"   This explains why verification fails!")
                            else:
                                print(f"   ✅ Only technical fields")
                                
                        except Exception as e:
                            print(f"❌ Failed to decode presentation definition: {e}")
                else:
                    print("❌ No presentation_definition found in redirect URL")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
        else:
            print(f"❌ Verifier form submission failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing current style: {e}")

def test_mock_verification_request():
    """Test a mock verification request to see what happens"""
    print("\n🧪 TESTING MOCK VERIFICATION WITH USER FIELD")
    print("=" * 60)
    
    # Create a mock VP token that only has technical fields (like current credentials)
    mock_technical_only_vp = {
        "verifiable_credential": {
            "values": {
                "jti": "test-jti",
                "signed_nonce": "test-signed-nonce", 
                "iss": "test-issuer",
                "nbf": 123456789,
                "sub": "test-subject",
                "validity_identifier": "test-validity",
                "nonce": "test-nonce",
                "exp": 123456789
                # NOTE: NO user fields like firstName, lastName, etc.
            },
            "total_messages": 8,
            "bbs_dpk": "test-bbs-dpk",
            "proof": "test-proof",
            "nonce": "test-nonce", 
            "proof_req": "test-proof-req"
        }
    }
    
    print("Mock credential contains only these fields:")
    for field in mock_technical_only_vp["verifiable_credential"]["values"].keys():
        print(f"   - {field}")
    
    print("\n❌ If verifier requests 'vc.credentialSubject.lastName':")
    print("   - Field is NOT in the credential")
    print("   - Verification will fail with 'Missing fields' error")
    print("   - This matches the actual error you're seeing")
    
    print("\n✅ If verifier only requests technical fields:")
    print("   - All fields are present in credential")
    print("   - Verification should succeed")
    print("   - This matches the working version behavior")

if __name__ == "__main__":
    print("🔍 VERIFIER ENDPOINT TESTING")
    print("Testing different approaches to understand selective disclosure issue")
    print("=" * 80)
    
    test_verifier_presentation_request_working_style()
    test_verifier_presentation_request_current_style()
    test_mock_verification_request()
    
    print("\n" + "=" * 80)
    print("🎯 SUMMARY:")
    print("The issue is that current verifier adds user fields to presentation definition,")
    print("but the credential being tested only contains technical fields.")
    print("\n🚀 SOLUTION:")
    print("1. Create credential with user data via web interface")
    print("2. Or temporarily revert to working version approach (technical fields only)")
    print("3. Or make user fields optional in verification logic")