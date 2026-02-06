#!/usr/bin/env python3
"""
Comprehensive test to understand the field mapping flow in the BBS+ verification
"""

import json

def test_ios_presentation_flow():
    """Simulate what the iOS wallet would send vs what backend expects"""
    
    print("=== BBS+ Field Mapping Analysis ===\n")
    
    # 1. Backend presentation definition (what backend checks for)
    backend_mandatory_fields = [
        "total_messages",
        "bbs_dpk", 
        "iss",
        "sub",
        "vc.expirationDate",
        "nonce",
        "signed_nonce",
        "validity_identifier"
    ]
    
    # 2. Backend presentation request mapping (what backend sends to iOS)
    field_mapping = {
        "total_messages": "totalMessages",
        "bbs_dpk": "bbsDPK", 
        "signed_nonce": "signedNonce",
        "validity_identifier": "validityIdentifier"
    }
    
    # 3. iOS presentation request (what iOS receives)
    ios_presentation_request = []
    for field in backend_mandatory_fields:
        ios_field = field_mapping.get(field, field)
        ios_presentation_request.append(ios_field)
    
    print("1. Backend mandatory fields (internal):")
    for field in backend_mandatory_fields:
        print(f"   - {field}")
    
    print("\n2. iOS presentation request fields (sent to wallet):")
    for field in ios_presentation_request:
        print(f"   - {field}")
    
    # 4. iOS RevealedCredentialJWT CodingKeys (what iOS sends back)
    ios_coding_keys = {
        "bbsDPK": "bbs_dpk",
        "totalMessages": "total_messages", 
        "signedNonce": "signed_nonce",
        "validityIdentifier": "validity_identifier",
        "iss": "iss",
        "sub": "sub",
        "nonce": "nonce"
    }
    
    # 5. Simulated iOS wallet response (what iOS actually sends)
    ios_wallet_response = {
        "total_messages": 17,  # iOS sends snake_case
        "bbs_dpk": "test_dpk_data",  # iOS sends snake_case
        "iss": "test_issuer",
        "sub": "test_subject",
        "vc": {"expirationDate": "2025-12-31T23:59:59Z"},
        "nonce": "test_nonce",
        "signed_nonce": "test_signed_nonce",  # iOS sends snake_case
        "validity_identifier": "test_validity_id"  # iOS sends snake_case
    }
    
    print("\n3. iOS wallet response fields (what wallet sends back):")
    for field in ios_wallet_response.keys():
        print(f"   - {field}")
    
    # 6. Check if backend mandatory field check would pass
    print("\n4. Backend mandatory field check analysis:")
    missing_fields = []
    for field in backend_mandatory_fields:
        if field == "vc.expirationDate":
            # Special handling for nested field
            if "vc" in ios_wallet_response and "expirationDate" in ios_wallet_response["vc"]:
                print(f"   ✅ {field}: Found (nested)")
            else:
                print(f"   ❌ {field}: Missing (nested)")
                missing_fields.append(field)
        else:
            if field in ios_wallet_response:
                print(f"   ✅ {field}: Found")
            else:
                print(f"   ❌ {field}: Missing")
                missing_fields.append(field)
    
    if not missing_fields:
        print("\n🎉 All mandatory fields would be found!")
    else:
        print(f"\n⚠️  Missing fields: {missing_fields}")
    
    # 7. Test with get_field_value function simulation
    print("\n5. Testing with get_field_value function:")
    
    def get_field_value_sim(data_dict, field_name):
        """Simulate the get_field_value function"""
        field_mappings = {
            'total_messages': ['total_messages', 'totalMessages'],
            'bbs_dpk': ['bbs_dpk', 'bbsDPK'],
            'signed_nonce': ['signed_nonce', 'signedNonce'],
            'validity_identifier': ['validity_identifier', 'validityIdentifier']
        }
        
        possible_names = field_mappings.get(field_name, [field_name])
        
        for name in possible_names:
            if name in data_dict:
                return data_dict[name]
        
        raise KeyError(f"Field '{field_name}' not found in data")
    
    for field in backend_mandatory_fields:
        try:
            if field == "vc.expirationDate":
                # Special handling for nested field
                if "vc" in ios_wallet_response and "expirationDate" in ios_wallet_response["vc"]:
                    value = ios_wallet_response["vc"]["expirationDate"]
                    print(f"   ✅ {field}: {value}")
                else:
                    print(f"   ❌ {field}: Missing (nested)")
            else:
                value = get_field_value_sim(ios_wallet_response, field)
                print(f"   ✅ {field}: {value}")
        except KeyError as e:
            print(f"   ❌ {field}: {e}")

if __name__ == "__main__":
    test_ios_presentation_flow()
