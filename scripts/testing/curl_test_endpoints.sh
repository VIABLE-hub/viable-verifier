#!/bin/bash

# VIABLE Credentials Endpoint Testing Script
# Tests all important endpoints with curl and saves the responses
# Author: Patrick Herbke (via Cursor AI)

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
LOG_DIR="logs/endpoints_$(date +%Y%m%d_%H%M%S)"
SUMMARY_FILE="$LOG_DIR/summary.md"
TENANTS=("root" "tub" "fub")

# Define endpoints to test
declare -A ENDPOINTS
ENDPOINTS["GET"]=(
  "/issuer/.well-known/openid-credential-issuer"
  "/verifier/.well-known/openid-configuration"
  "/vcstatus"
  "/settings"
  "/health"
)

# Sample JSON payloads for POST requests
ISSUER_PAYLOAD='{
  "firstName": "Test",
  "lastName": "User",
  "studentId": "123456",
  "studentIdPrefix": "TU",
  "email": "test.user@example.com",
  "dateOfBirth": "2000-01-01",
  "studyProgram": "Computer Science",
  "faculty": "Faculty of Computer Science",
  "enrollmentDate": "2020-10-01",
  "expectedGraduation": "2024-09-30"
}'

VERIFIER_PAYLOAD='{
  "presentation": {
    "credential": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
    "proof": {
      "type": "BbsBlsSignatureProof2020",
      "created": "2023-01-01T00:00:00Z",
      "proofPurpose": "authentication",
      "verificationMethod": "did:key:z...",
      "challenge": "1234567890",
      "nonce": "abcdefghijklmnopqrstuvwxyz"
    }
  }
}'

# Function to log messages
log() {
  local level=$1
  local message=$2
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  
  case $level in
    "INFO")
      echo -e "${GREEN}[INFO]${NC} $timestamp - $message"
      ;;
    "WARN")
      echo -e "${YELLOW}[WARN]${NC} $timestamp - $message"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR]${NC} $timestamp - $message"
      ;;
    "STEP")
      echo -e "\n${BLUE}==== $message ====${NC}"
      ;;
    *)
      echo -e "$timestamp - $message"
      ;;
  esac
}

# Function to test a GET endpoint
test_get_endpoint() {
  local tenant=$1
  local endpoint=$2
  local port=$3
  local url="https://localhost:$port$endpoint"
  local output_file="$LOG_DIR/${tenant}_GET_$(echo "$endpoint" | tr '/' '_').json"
  local status_file="$LOG_DIR/${tenant}_GET_$(echo "$endpoint" | tr '/' '_').status"
  
  log "INFO" "Testing GET $url"
  
  # Make the request
  local start_time=$(date +%s)
  curl -k -s -o "$output_file" -w "%{http_code}" "$url" > "$status_file" 2>/dev/null
  local status=$(cat "$status_file")
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  # Check if the request was successful
  if [[ "$status" == 2* ]]; then
    log "INFO" "✅ GET $url returned status $status in ${duration}s"
    echo "| $tenant | GET | $endpoint | ✅ $status | ${duration}s |" >> "$SUMMARY_FILE"
    return 0
  else
    log "ERROR" "❌ GET $url returned status $status in ${duration}s"
    echo "| $tenant | GET | $endpoint | ❌ $status | ${duration}s |" >> "$SUMMARY_FILE"
    return 1
  fi
}

# Function to test a POST endpoint
test_post_endpoint() {
  local tenant=$1
  local endpoint=$2
  local port=$3
  local payload=$4
  local url="https://localhost:$port$endpoint"
  local output_file="$LOG_DIR/${tenant}_POST_$(echo "$endpoint" | tr '/' '_').json"
  local status_file="$LOG_DIR/${tenant}_POST_$(echo "$endpoint" | tr '/' '_').status"
  
  log "INFO" "Testing POST $url"
  
  # Make the request
  local start_time=$(date +%s)
  curl -k -s -X POST -H "Content-Type: application/json" -d "$payload" -o "$output_file" -w "%{http_code}" "$url" > "$status_file" 2>/dev/null
  local status=$(cat "$status_file")
  local end_time=$(date +%s)
  local duration=$((end_time - start_time))
  
  # Check if the request was successful
  if [[ "$status" == 2* ]]; then
    log "INFO" "✅ POST $url returned status $status in ${duration}s"
    echo "| $tenant | POST | $endpoint | ✅ $status | ${duration}s |" >> "$SUMMARY_FILE"
    return 0
  else
    log "ERROR" "❌ POST $url returned status $status in ${duration}s"
    echo "| $tenant | POST | $endpoint | ❌ $status | ${duration}s |" >> "$SUMMARY_FILE"
    return 1
  fi
}

# Main function
main() {
  # Create log directory
  mkdir -p "$LOG_DIR"
  
  # Create summary file
  echo "# VIABLE Credentials Endpoint Test Summary" > "$SUMMARY_FILE"
  echo "Date: $(date)" >> "$SUMMARY_FILE"
  echo "" >> "$SUMMARY_FILE"
  echo "| Tenant | Method | Endpoint | Status | Duration |" >> "$SUMMARY_FILE"
  echo "|--------|--------|----------|--------|----------|" >> "$SUMMARY_FILE"
  
  # Define ports for each tenant
  declare -A ports
  ports["root"]="8080"
  ports["tub"]="8081"
  ports["fub"]="8082"
  
  # Test GET endpoints
  log "STEP" "Testing GET endpoints"
  for tenant in "${TENANTS[@]}"; do
    for endpoint in "${ENDPOINTS["GET"][@]}"; do
      test_get_endpoint "$tenant" "$endpoint" "${ports[$tenant]}"
    done
  done
  
  # Test POST endpoints
  log "STEP" "Testing POST endpoints"
  for tenant in "${TENANTS[@]}"; do
    # Test issuer endpoint
    test_post_endpoint "$tenant" "/issuer" "${ports[$tenant]}" "$ISSUER_PAYLOAD"
    
    # Test verifier endpoint
    test_post_endpoint "$tenant" "/verifier" "${ports[$tenant]}" "$VERIFIER_PAYLOAD"
  done
  
  # Check for any failures in the summary file
  log "STEP" "Checking for failures"
  if grep -q "❌" "$SUMMARY_FILE"; then
    log "ERROR" "❌ Some endpoint tests failed. See $SUMMARY_FILE for details."
    echo "" >> "$SUMMARY_FILE"
    echo "## ❌ OVERALL RESULT: FAILED" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "Some endpoint tests failed. Please fix the issues before deploying." >> "$SUMMARY_FILE"
    exit 1
  else
    log "INFO" "✅ All endpoint tests passed!"
    echo "" >> "$SUMMARY_FILE"
    echo "## ✅ OVERALL RESULT: PASSED" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
    echo "All endpoint tests passed. Ready for deployment!" >> "$SUMMARY_FILE"
  fi
  
  # Print summary location
  log "INFO" "Summary report available at: $SUMMARY_FILE"
  log "INFO" "Response files available in: $LOG_DIR"
}

# Run main function
main 