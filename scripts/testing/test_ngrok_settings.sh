#!/bin/bash
# NGROK Settings Test Script
# Tests setting, reading, and unsetting NGROK configuration for Veritas tenant

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🧪 NGROK Settings Test Suite${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
BASE_URL="https://localhost:8080"
API_ENDPOINT="$BASE_URL/api/network"
TEST_NGROK_URL="https://test-veritas-123.ngrok-free.app"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=6

# Function to print test result
print_result() {
    local test_name=$1
    local result=$2
    local message=$3
    
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $test_name"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $test_name - $message"
        ((TESTS_FAILED++))
    fi
}

# Function to make API call
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -k -s -X "$method" "$endpoint"
    else
        curl -k -s -X "$method" "$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

echo -e "${YELLOW}📋 Prerequisites:${NC}"
echo "   • Server must be running on $BASE_URL"
echo "   • Tenant: veritas (started with 'make dev-veritas')"
echo ""
echo -e "${YELLOW}Starting tests...${NC}"
echo ""

# Test 1: Get initial network settings
echo -e "${BLUE}Test 1: Get initial network settings${NC}"
RESPONSE=$(api_call GET "$API_ENDPOINT")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")

if [ "$STATUS" = "success" ]; then
    print_result "Get initial settings" 0
    echo "   Initial connection mode: $(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network_settings', {}).get('connection_mode', 'unknown'))")"
else
    print_result "Get initial settings" 1 "API returned error status"
fi
echo ""

# Test 2: Set NGROK URL
echo -e "${BLUE}Test 2: Set NGROK URL${NC}"
REQUEST_DATA='{
    "use_ngrok": true,
    "ngrok_url": "'$TEST_NGROK_URL'",
    "connection_mode": "ngrok"
}'

RESPONSE=$(api_call POST "$API_ENDPOINT" "$REQUEST_DATA")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")
SERVER_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('updated_config', {}).get('server_url', ''))")

if [ "$STATUS" = "success" ] && [ "$SERVER_URL" = "$TEST_NGROK_URL" ]; then
    print_result "Set NGROK URL" 0
    echo "   Server URL: $SERVER_URL"
else
    print_result "Set NGROK URL" 1 "Failed to set NGROK URL or URL mismatch"
fi
echo ""

# Test 3: Verify NGROK settings persisted
echo -e "${BLUE}Test 3: Verify NGROK settings persisted${NC}"
sleep 1
RESPONSE=$(api_call GET "$API_ENDPOINT")
USE_NGROK=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network_settings', {}).get('use_ngrok', False))")
NGROK_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network_settings', {}).get('ngrok_url', ''))")

if [ "$USE_NGROK" = "True" ] && [ "$NGROK_URL" = "$TEST_NGROK_URL" ]; then
    print_result "Verify NGROK persistence" 0
    echo "   use_ngrok: $USE_NGROK"
    echo "   ngrok_url: $NGROK_URL"
else
    print_result "Verify NGROK persistence" 1 "Settings did not persist"
fi
echo ""

# Test 4: Verify URLs updated to use NGROK
echo -e "${BLUE}Test 4: Verify URLs updated to use NGROK${NC}"
ISSUER_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('computed_urls', {}).get('issuer_url', ''))")
VERIFIER_URL=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('computed_urls', {}).get('verifier_url', ''))")

if [[ "$ISSUER_URL" == "$TEST_NGROK_URL"* ]] && [[ "$VERIFIER_URL" == "$TEST_NGROK_URL"* ]]; then
    print_result "Verify URLs use NGROK" 0
    echo "   Issuer URL: $ISSUER_URL"
    echo "   Verifier URL: $VERIFIER_URL"
else
    print_result "Verify URLs use NGROK" 1 "URLs not updated to NGROK"
fi
echo ""

# Test 5: Unset NGROK (return to local mode)
echo -e "${BLUE}Test 5: Unset NGROK URL (return to local)${NC}"
REQUEST_DATA='{
    "use_ngrok": false,
    "ngrok_url": "",
    "connection_mode": "local"
}'

RESPONSE=$(api_call POST "$API_ENDPOINT" "$REQUEST_DATA")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'error'))")
USE_NGROK=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('updated_config', {}).get('network_settings', {}).get('use_ngrok', True))")

if [ "$STATUS" = "success" ] && [ "$USE_NGROK" = "False" ]; then
    print_result "Unset NGROK URL" 0
    echo "   use_ngrok: $USE_NGROK"
else
    print_result "Unset NGROK URL" 1 "Failed to unset NGROK"
fi
echo ""

# Test 6: Verify return to local mode
echo -e "${BLUE}Test 6: Verify return to local mode${NC}"
sleep 1
RESPONSE=$(api_call GET "$API_ENDPOINT")
CONNECTION_MODE=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network_info', {}).get('connection_mode', 'unknown'))")
USE_NGROK=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('network_info', {}).get('use_ngrok', True))")

if [ "$CONNECTION_MODE" = "local" ] && [ "$USE_NGROK" = "False" ]; then
    print_result "Verify local mode" 0
    echo "   connection_mode: $CONNECTION_MODE"
    echo "   use_ngrok: $USE_NGROK"
else
    print_result "Verify local mode" 1 "Not in local mode"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo -e "${GREEN}✅ NGROK configuration is working correctly:${NC}"
    echo "   • Setting NGROK URL ✓"
    echo "   • Unsetting NGROK URL ✓"
    echo "   • Settings persistence ✓"
    echo "   • URL dynamic updates ✓"
    echo "   • Connection mode switching ✓"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi

