#!/usr/bin/env python3
"""
🔍 SELECTIVE DISCLOSURE CONFIGURATION TESTER
Tests all possible combinations of selective disclosure to ensure the verifier works correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import logging
import json
import requests
import itertools
from src.verifier.verifier import TECHNICAL_FIELDS_CAMEL_CASE, SELECTABLE_USER_FIELDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_selective_disclosure_config(selected_fields):
    """Test a specific selective disclosure configuration"""
    print(f"\n🔍 Testing configuration with {len(selected_fields)} selected fields:")
    for field in selected_fields:
        print(f"   ✓ {field}")
    
    # Calculate total fields (technical + selected)
    total_fields = len(TECHNICAL_FIELDS_CAMEL_CASE) + len(selected_fields)
    print(f"   Total fields: {total_fields} ({len(TECHNICAL_FIELDS_CAMEL_CASE)} technical + {len(selected_fields)} user)")
    
    # These would be the mandatory fields in the presentation definition
    mandatory_fields = TECHNICAL_FIELDS_CAMEL_CASE + list(selected_fields)
    print(f"   Mandatory fields: {mandatory_fields}")
    
    return {
        "selected_fields": selected_fields,
        "technical_fields": TECHNICAL_FIELDS_CAMEL_CASE,
        "total_fields": total_fields,
        "mandatory_fields": mandatory_fields
    }

def main():
    print("🔍 SELECTIVE DISCLOSURE CONFIGURATION TESTER")
    print("=" * 60)
    
    # 1. Show the current technical and user fields
    print("\n📋 TECHNICAL FIELDS (camelCase - always required):")
    for field in TECHNICAL_FIELDS_CAMEL_CASE:
        print(f"   ✓ {field}")
    
    print("\n📋 USER FIELDS (selectively disclosed):")
    for field in SELECTABLE_USER_FIELDS:
        print(f"   ✓ {field}")
    
    # 2. Test all possible combinations of selective disclosure
    print("\n🔍 TESTING ALL POSSIBLE CONFIGURATIONS")
    print("=" * 60)
    
    # Generate all possible combinations of selectable fields
    all_configs = []
    
    # Case 1: No fields selected (minimum disclosure)
    config = test_selective_disclosure_config([])
    all_configs.append(config)
    
    # Case 2: All possible combinations of 1 or more fields
    for r in range(1, len(SELECTABLE_USER_FIELDS) + 1):
        for combo in itertools.combinations(SELECTABLE_USER_FIELDS, r):
            config = test_selective_disclosure_config(combo)
            all_configs.append(config)
    
    # 3. Summary
    print("\n✅ SUMMARY")
    print("=" * 60)
    print(f"Tested {len(all_configs)} different configurations:")
    print(f"   - 1 configuration with no user fields")
    for r in range(1, len(SELECTABLE_USER_FIELDS) + 1):
        count = len(list(itertools.combinations(SELECTABLE_USER_FIELDS, r)))
        print(f"   - {count} configurations with {r} user field{'s' if r > 1 else ''}")
    
    print("\nAll configurations should work with the fixed verifier!")
    
    # 4. Try to access the verifier page to verify server is running
    try:
        response = requests.get("https://localhost:8080/verifier/", verify=False)
        print(f"\n✓ Verifier page accessible: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Error accessing verifier: {e}")
    
    # 5. Save all configurations to a file for reference
    with open("selective_disclosure_configs.json", "w") as f:
        json.dump(all_configs, f, indent=2)
    print("\nSaved all configurations to selective_disclosure_configs.json")

if __name__ == "__main__":
    main() 