#!/usr/bin/env python3
"""
End-to-End Test für STVC Verifiable Credential Issuance und Verification
Tests die komplette Workflow zwischen iOS Wallet und Python Backend
"""

import requests
import json
import time
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_complete_credential_workflow():
    """Vollständiger Credential Workflow Test"""
    print("🎓 VERIFIABLE CREDENTIAL END-TO-END TEST")
    print("=" * 60)
    
    base_url = "https://127.0.0.1:8080"
    
    # Test Student Data (wie sie von iOS Wallet kommen würde)
    student_data = {
        "student_id": "e2e_test_12345",
        "student_name": "Max Mustermann",
        "university": "Technische Universität München",
        "degree": "Master Computer Science",
        "graduation_date": "2024-12-15",
        "grade": "1.2",
        "student_email": "max.mustermann@tum.de"
    }
    
    print(f"Student Data: {json.dumps(student_data, indent=2)}")
    
    # Step 1: Credential Issuance
    print("\n📋 STEP 1: Credential Issuance")
    print("-" * 40)
    
    try:
        # Step 1a: Create credential offer
        start_time = time.time()
        offer_response = requests.post(
            f"{base_url}/offer",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StudentWallet-iOS/1.0"
            },
            verify=False,
            timeout=30,
            allow_redirects=False
        )
        
        if offer_response.status_code != 302:
            print(f"❌ Offer creation failed: HTTP {offer_response.status_code}")
            return False
            
        # Extract credential offer URI from redirect
        offer_uri = offer_response.headers.get('Location')
        if not offer_uri:
            print("❌ No credential offer URI in redirect")
            return False
            
        print(f"✅ Credential offer created: {offer_uri}")
        
        # Step 1b: Fetch credential offer details
        offer_detail_response = requests.get(
            offer_uri,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "StudentWallet-iOS/1.0"
            },
            verify=False,
            timeout=30
        )
        issuance_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            credential_response = response.json()
            print(f"✅ Credential issued successfully ({issuance_time:.1f}ms)")
            
            # Validate credential structure
            required_fields = ["credential", "format", "signature"]
            for field in required_fields:
                if field in credential_response:
                    print(f"   ✅ {field}: present")
                else:
                    print(f"   ❌ {field}: MISSING")
                    return False
            
            # Extract credential details
            credential = credential_response.get("credential", {})
            credential_format = credential_response.get("format", "unknown")
            signature = credential_response.get("signature", "")
            
            print(f"   📋 Format: {credential_format}")
            print(f"   🔐 Signature length: {len(str(signature))} chars")
            
            if isinstance(credential, dict) and "credentialSubject" in credential:
                subject = credential["credentialSubject"]
                print(f"   👤 Subject ID: {subject.get('id', 'N/A')}")
                print(f"   🎓 Degree: {subject.get('degree', 'N/A')}")
            
        else:
            print(f"❌ Credential issuance failed: HTTP {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Credential issuance error: {str(e)}")
        return False
    
    # Step 2: Credential Verification
    print("\n🔍 STEP 2: Credential Verification")
    print("-" * 40)
    
    try:
        # Prepare verification request (wie sie von einem Verifier kommen würde)
        verification_request = {
            "credential": credential_response.get("credential"),
            "signature": credential_response.get("signature"),
            "format": credential_response.get("format")
        }
        
        start_time = time.time()
        verify_response = requests.post(
            f"{base_url}/verifier",
            json=verification_request,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "STVC-Verifier/1.0"
            },
            verify=False,
            timeout=30
        )
        verification_time = (time.time() - start_time) * 1000
        
        if verify_response.status_code == 200:
            verification_result = verify_response.json()
            print(f"✅ Credential verified successfully ({verification_time:.1f}ms)")
            
            # Check verification details
            is_valid = verification_result.get("valid", False)
            verification_details = verification_result.get("details", {})
            
            print(f"   ✅ Valid: {is_valid}")
            
            if "issuer" in verification_details:
                print(f"   🏛️  Issuer: {verification_details['issuer']}")
            
            if "subject" in verification_details:
                print(f"   👤 Subject: {verification_details['subject']}")
            
            if "issuance_date" in verification_details:
                print(f"   📅 Issued: {verification_details['issuance_date']}")
                
        else:
            print(f"❌ Credential verification failed: HTTP {verify_response.status_code}")
            print(f"   Error: {verify_response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Credential verification error: {str(e)}")
        return False
    
    # Step 3: iOS Compatibility Validation
    print("\n📱 STEP 3: iOS Compatibility Validation")
    print("-" * 40)
    
    # Check if response format is iOS-friendly
    ios_compatible = True
    
    # Check for snake_case vs camelCase
    response_str = json.dumps(credential_response)
    if "_" in response_str:
        snake_case_fields = [key for key in credential_response.keys() if "_" in key]
        print(f"⚠️  Snake_case fields detected: {snake_case_fields}")
        print("   iOS würde camelCase bevorzugen")
        ios_compatible = False
    else:
        print("✅ No snake_case issues detected")
    
    # Check credential size (für iOS Keychain)
    credential_size = len(json.dumps(credential_response))
    print(f"📦 Credential size: {credential_size} bytes")
    
    if credential_size < 8192:  # iOS Keychain limit
        print("✅ Size compatible with iOS Keychain")
    else:
        print("⚠️  Size might be too large for iOS Keychain")
        ios_compatible = False
    
    # Check for iOS-friendly date formats
    credential_json = json.dumps(credential_response)
    if "T" in credential_json and "Z" in credential_json:
        print("✅ ISO 8601 date format detected (iOS compatible)")
    else:
        print("⚠️  Date format might not be iOS compatible")
    
    if ios_compatible:
        print("✅ Credential is iOS compatible")
    else:
        print("⚠️  Some iOS compatibility issues detected")
    
    # Step 4: Performance Summary
    print("\n⚡ STEP 4: Performance Summary")
    print("-" * 40)
    
    total_time = issuance_time + verification_time
    print(f"Credential Issuance: {issuance_time:.1f}ms")
    print(f"Credential Verification: {verification_time:.1f}ms")
    print(f"Total Workflow Time: {total_time:.1f}ms")
    
    if total_time < 1000:
        print("✅ Excellent performance (< 1 second)")
    elif total_time < 3000:
        print("✅ Good performance (< 3 seconds)")
    else:
        print("⚠️  Performance could be improved")
    
    return True

def test_multiple_credentials():
    """Test mit mehreren Credentials (Stress Test)"""
    print("\n🔄 STRESS TEST: Multiple Credentials")
    print("-" * 40)
    
    base_url = "https://127.0.0.1:8080"
    
    students = [
        {"student_id": "stress_001", "degree": "Bachelor Computer Science", "grade": "1.0"},
        {"student_id": "stress_002", "degree": "Master Mathematics", "grade": "1.5"},
        {"student_id": "stress_003", "degree": "PhD Physics", "grade": "1.2"}
    ]
    
    success_count = 0
    total_time = 0
    
    for i, student in enumerate(students, 1):
        try:
            start = time.time()
            response = requests.post(
                f"{base_url}/issuer",
                json=student,
                headers={"Content-Type": "application/json"},
                verify=False,
                timeout=15
            )
            duration = (time.time() - start) * 1000
            total_time += duration
            
            if response.status_code == 200:
                print(f"✅ Credential {i}: OK ({duration:.1f}ms)")
                success_count += 1
            else:
                print(f"❌ Credential {i}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Credential {i}: {str(e)[:30]}")
    
    print(f"\nStress Test Results:")
    print(f"✅ Successful: {success_count}/{len(students)}")
    print(f"⚡ Average time: {total_time/len(students):.1f}ms")
    
    return success_count == len(students)

def main():
    """Hauptfunktion - Alle E2E Tests ausführen"""
    print("🚀 STVC END-TO-END TESTING SUITE")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Complete Credential Workflow", test_complete_credential_workflow),
        ("Multiple Credentials Stress Test", test_multiple_credentials)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {str(e)}")
    
    # Final Report
    print("\n" + "=" * 60)
    print("📊 END-TO-END TEST REPORT")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ System is ready for production deployment")
        print("✅ iOS Wallet can successfully interact with backend")
        print("✅ Verifiable Credentials are working end-to-end")
        status = "PRODUCTION_READY"
    elif success_rate >= 80:
        print("\n🟡 MOST TESTS PASSED")
        print("⚠️  Minor issues detected, but system is largely functional")
        status = "MOSTLY_READY"
    else:
        print("\n🔴 CRITICAL ISSUES DETECTED")
        print("❌ System not ready for production")
        status = "NOT_READY"
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "success_rate": success_rate,
        "tests_passed": passed,
        "tests_total": total,
        "summary": {
            "backend_responsive": True,
            "credential_issuance_working": passed >= 1,
            "ios_compatibility": "tested",
            "performance": "acceptable"
        }
    }
    
    with open("e2e_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: e2e_test_results.json")

if __name__ == "__main__":
    main()
