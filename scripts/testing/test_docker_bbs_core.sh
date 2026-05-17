#!/bin/bash

# BBS+ Core Docker Testing Script
# Tests ONLY BBS+ functionality in Docker containers - STEP BY STEP
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
LOG_DIR="logs/bbs_docker_test_$(date +%Y%m%d_%H%M%S)"
SUMMARY_FILE="$LOG_DIR/bbs_summary.md"
TENANTS=("root" "tub" "fub")
DOCKER_COMPOSE_FILE="deploy/configs/docker-compose.yml"

echo -e "${BLUE}┌─────────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ BBS+ CORE DOCKER TESTING - STEP BY STEP                │${NC}"
echo -e "${BLUE}│ Testing ONLY BBS+ functionality in containers          │${NC}"
echo -e "${BLUE}└─────────────────────────────────────────────────────────┘${NC}"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
  local level=$1
  local message=$2
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  echo -e "${timestamp} - ${level} - ${message}" | tee -a "$LOG_DIR/test.log"
}

# Function to run command with logging
run_with_logging() {
  local description=$1
  local command=$2
  
  log "INFO" "🚀 Running: $description"
  local start_time=$(date +%s)
  
  if bash -c "$command" >> "$LOG_DIR/test.log" 2>&1; then
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log "INFO" "✅ $description completed successfully in ${duration}s"
    return 0
  else
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log "ERROR" "❌ $description failed with exit code $exit_code in ${duration}s"
    return 1
  fi
}

# Function to test BBS+ in a specific container
test_bbs_in_container() {
  local tenant=$1
  local container_name="viable-credentials-$tenant"
  
  log "INFO" "🧪 Testing BBS+ in container: $container_name"
  
  # Test 1: Check if bbs_core module can be imported
  log "INFO" "   📦 Test 1: BBS+ module import"
  if docker exec "$container_name" python3 -c "
import sys
sys.path.insert(0, '/app')
try:
    import bbs_core
    print('✅ BBS+ core imported successfully')
    print(f'✅ Module path: {bbs_core.__file__}')
except Exception as e:
    print(f'❌ BBS+ core import failed: {e}')
    sys.exit(1)
" >> "$LOG_DIR/test.log" 2>&1; then
    log "INFO" "   ✅ BBS+ module import: PASSED"
  else
    log "ERROR" "   ❌ BBS+ module import: FAILED"
    return 1
  fi
  
  # Test 2: Check BBS+ functions availability
  log "INFO" "   🔧 Test 2: BBS+ functions availability"
  if docker exec "$container_name" python3 -c "
import sys
sys.path.insert(0, '/app')
import bbs_core
# Check for UniFFI-generated classes instead of old function names
required_classes = ['KeyPair', 'SignRequest', 'VerifyRequest', 'GenerateKeyPair']
available_functions = [attr for attr in dir(bbs_core) if not attr.startswith('_')]
print(f'Available functions: {available_functions}')
missing = [f for f in required_classes if f not in available_functions]
if missing:
    print(f'❌ Missing classes: {missing}')
    sys.exit(1)
else:
    print('✅ All required BBS+ classes available')
" >> "$LOG_DIR/test.log" 2>&1; then
    log "INFO" "   ✅ BBS+ functions availability: PASSED"
  else
    log "ERROR" "   ❌ BBS+ functions availability: FAILED"
    return 1
  fi
  
  # Test 3: Test key generation
  log "INFO" "   🔑 Test 3: BBS+ key generation"
  if docker exec "$container_name" python3 -c "
import sys
sys.path.insert(0, '/app')
import bbs_core
try:
    # Test key generation using correct UniFFI two-step process
    key_generator = bbs_core.GenerateKeyPair()
    keypair = key_generator.generate_key_pair()
    print(f'✅ KeyPair created successfully using GenerateKeyPair().generate_key_pair()')
    
    # Check if keys have the expected attributes for UniFFI-generated objects
    # Try Linux/Docker attribute names first
    if hasattr(keypair, 'dpub_key_bytes') and hasattr(keypair, 'priv_key_bytes'):
        print('✅ Found Linux/Docker BBS+ key attributes (dpub_key_bytes, priv_key_bytes)')
    # Try macOS attribute names as fallback
    elif hasattr(keypair, 'public_key') and hasattr(keypair, 'secret_key'):
        print('✅ Found macOS BBS+ key attributes (public_key, secret_key)')
    else:
        print('❌ No expected key attributes found')
        available_attrs = [attr for attr in dir(keypair) if not attr.startswith('_')]
        print(f'Available attributes: {available_attrs}')
        sys.exit(1)
        
    print('✅ BBS+ key generation test passed')
except Exception as e:
    print(f'❌ BBS+ key generation failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
" >> "$LOG_DIR/test.log" 2>&1; then
    log "INFO" "   ✅ BBS+ key generation: PASSED"
  else
    log "ERROR" "   ❌ BBS+ key generation: FAILED"
    return 1
  fi
  
  # Test 4: Test tenant-specific key loading
  log "INFO" "   🏛️ Test 4: Tenant-specific key loading"
  if docker exec "$container_name" python3 -c "
import sys
sys.path.insert(0, '/app')
import os
os.environ['TENANT_ID'] = '$tenant'

try:
    from src.issuer.tenant_key_generator import get_current_tenant_keys
    keys = get_current_tenant_keys()
    print(f'✅ Tenant keys loaded for: $tenant')
    print(f'✅ Keys type: {type(keys)}')
    print(f'✅ Available key attributes: {[attr for attr in dir(keys) if not attr.startswith(\"_\")]}')
except Exception as e:
    print(f'❌ Tenant key loading failed: {e}')
    sys.exit(1)
" >> "$LOG_DIR/test.log" 2>&1; then
    log "INFO" "   ✅ Tenant-specific key loading: PASSED"
  else
    log "ERROR" "   ❌ Tenant-specific key loading: FAILED"
    return 1
  fi
  
  log "INFO" "🎉 All BBS+ tests PASSED for container: $container_name"
  return 0
}

# Function to generate summary
generate_summary() {
  local total_tests=0
  local passed_tests=0
  
  echo "# BBS+ Docker Test Summary" > "$SUMMARY_FILE"
  echo "Generated: $(date)" >> "$SUMMARY_FILE"
  echo "" >> "$SUMMARY_FILE"
  
  for tenant in "${TENANTS[@]}"; do
    total_tests=$((total_tests + 1))
    if grep -q "All BBS+ tests PASSED for container: viable-credentials-$tenant" "$LOG_DIR/test.log"; then
      passed_tests=$((passed_tests + 1))
      echo "- ✅ **$tenant**: BBS+ core functionality working" >> "$SUMMARY_FILE"
    else
      echo "- ❌ **$tenant**: BBS+ core functionality failed" >> "$SUMMARY_FILE"
    fi
  done
  
  echo "" >> "$SUMMARY_FILE"
  echo "## Summary" >> "$SUMMARY_FILE"
  echo "- **Total Tenants:** $total_tests" >> "$SUMMARY_FILE"
  echo "- **Passed:** $passed_tests" >> "$SUMMARY_FILE"
  echo "- **Failed:** $((total_tests - passed_tests))" >> "$SUMMARY_FILE"
  echo "- **Success Rate:** $([[ $total_tests -gt 0 ]] && echo \"$(( passed_tests * 100 / total_tests ))%\" || echo \"N/A\")" >> "$SUMMARY_FILE"
  
  echo "" >> "$SUMMARY_FILE"
  echo "## Detailed Logs" >> "$SUMMARY_FILE"
  echo "Full test logs available at: \`$LOG_DIR/test.log\`" >> "$SUMMARY_FILE"
}

# Main execution
main() {
  log "INFO" "🚀 Starting BBS+ Docker core testing..."
  
  # Step 1: Ensure Linux BBS+ build is applied
  log "INFO" "🐧 Step 1: Applying Linux BBS+ Build for Docker..."
  if ! run_with_logging "Apply Linux BBS+ Build" "make use-linux-bbs"; then
    log "ERROR" "❌ Failed to apply Linux BBS+ build"
    exit 1
  fi
  
  # Step 2: Check if containers are running
  log "INFO" "🐳 Step 2: Checking Docker containers..."
  if ! docker compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
    log "INFO" "⚠️ Containers not running, starting them..."
    if ! run_with_logging "Start Docker Containers" "docker compose -f $DOCKER_COMPOSE_FILE up -d"; then
      log "ERROR" "❌ Failed to start Docker containers"
      exit 1
    fi
    
    # Wait for containers to be ready
    log "INFO" "⏰ Waiting 30 seconds for containers to initialize..."
    sleep 30
  fi
  
  # Step 3: Test BBS+ in each container
  log "INFO" "🧪 Step 3: Testing BBS+ core in each container..."
  local overall_success=true
  
  for tenant in "${TENANTS[@]}"; do
    echo
    log "INFO" "📋 Testing tenant: $tenant"
    
    if ! test_bbs_in_container "$tenant"; then
      log "ERROR" "❌ BBS+ tests failed for tenant: $tenant"
      overall_success=false
    else
      log "INFO" "✅ BBS+ tests passed for tenant: $tenant"
    fi
  done
  
  # Step 4: Generate summary
  log "INFO" "📊 Step 4: Generating test summary..."
  generate_summary
  
  # Display summary
  echo
  echo -e "${YELLOW}==================== TEST SUMMARY ====================${NC}"
  cat "$SUMMARY_FILE"
  echo -e "${YELLOW}=======================================================${NC}"
  
  if $overall_success; then
    log "INFO" "🎉 ALL BBS+ DOCKER TESTS PASSED!"
    echo -e "${GREEN}✅ BBS+ core is working correctly in all Docker containers${NC}"
    echo -e "${GREEN}🚀 Ready for production deployment!${NC}"
    exit 0
  else
    log "ERROR" "❌ SOME BBS+ DOCKER TESTS FAILED!"
    echo -e "${RED}❌ BBS+ core issues detected in Docker containers${NC}"
    echo -e "${RED}🔧 Please check the logs and fix the issues before deployment${NC}"
    exit 1
  fi
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
  log "ERROR" "❌ Docker is not available. Please install Docker first."
  exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
  log "ERROR" "❌ Docker Compose is not available. Please install Docker Compose first."
  exit 1
fi

# Run main function
main 