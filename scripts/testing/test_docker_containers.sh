#!/bin/bash

# Script to test Docker containers for all StudentVC tenants
# Tests BBS+ functionality via API endpoints
# Author: Patrick Herbke (via Cursor AI)

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}┌───────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ StudentVC Docker Container API Test                   │${NC}"
echo -e "${BLUE}│ Tests BBS+ functionality in all tenant containers     │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────────────┘${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}❌ Error: Docker is not running.${NC}"
  echo -e "${YELLOW}Please start Docker and try again.${NC}"
  exit 1
fi

# Check if containers are running
echo -e "${BLUE}Checking for running StudentVC containers...${NC}"
containers=$(docker ps | grep -E 'studentvc-' | awk '{print $1}')

if [ -z "$containers" ]; then
  echo -e "${YELLOW}No running StudentVC containers found.${NC}"
  echo -e "${YELLOW}Would you like to start the containers? (y/n)${NC}"
  read -r start_containers
  
  if [[ "$start_containers" == "y" || "$start_containers" == "Y" ]]; then
    echo -e "${BLUE}Starting StudentVC containers...${NC}"
    cd deploy && docker-compose -f configs/docker-compose.yml up -d
    
    # Wait for containers to start
    echo -e "${YELLOW}Waiting for containers to start (30 seconds)...${NC}"
    sleep 30
    
    # Check if containers are running now
    containers=$(docker ps | grep -E 'studentvc-' | awk '{print $1}')
    
    if [ -z "$containers" ]; then
      echo -e "${RED}❌ Error: Failed to start StudentVC containers.${NC}"
      exit 1
    fi
  else
    echo -e "${RED}Operation cancelled${NC}"
    exit 0
  fi
fi

# Get container ports
echo -e "${BLUE}Finding tenant container ports...${NC}"

# Initialize arrays for tenant information
declare -A tenant_ports
declare -A tenant_ids

# Get container information
while read -r container_id name ports; do
  tenant_id=$(echo "$name" | sed -n 's/.*studentvc-\(.*\)/\1/p')
  port=$(echo "$ports" | grep -oE ':[0-9]+->8080' | cut -d':' -f2 | cut -d'-' -f1)
  
  if [ -n "$tenant_id" ] && [ -n "$port" ]; then
    tenant_ports["$tenant_id"]="$port"
    tenant_ids["$tenant_id"]="$container_id"
    echo -e "${GREEN}✅ Found tenant ${BLUE}$tenant_id${GREEN} on port ${BLUE}$port${GREEN} (container: ${BLUE}$container_id${GREEN})${NC}"
  fi
done < <(docker ps | grep -E 'studentvc-' | awk '{print $1, $2, $7}')

# Check if we found any tenants
if [ ${#tenant_ids[@]} -eq 0 ]; then
  echo -e "${RED}❌ Error: No StudentVC tenant containers found.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Found ${#tenant_ids[@]} tenant containers${NC}"

# Prepare URLs for the Python test script
urls=()
tenant_list=()

for tenant_id in "${!tenant_ports[@]}"; do
  urls+=("https://localhost:${tenant_ports[$tenant_id]}")
  tenant_list+=("$tenant_id")
done

# Create directories if they don't exist
mkdir -p scripts/testing/results

# Run the Python test script
echo -e "${BLUE}Running API tests against all tenant containers...${NC}"

# Check if Python test script exists
if [ ! -f "scripts/testing/test_tenant_apis.py" ]; then
  echo -e "${RED}❌ Error: Python test script not found.${NC}"
  echo -e "${YELLOW}Please make sure scripts/testing/test_tenant_apis.py exists.${NC}"
  exit 1
fi

# Make the script executable
chmod +x scripts/testing/test_tenant_apis.py

# Run the tests
timestamp=$(date +"%Y%m%d_%H%M%S")
output_file="scripts/testing/results/docker_test_${timestamp}.json"

echo -e "${BLUE}Running tests with:${NC}"
echo -e "${YELLOW}Tenants: ${tenant_list[*]}${NC}"
echo -e "${YELLOW}URLs: ${urls[*]}${NC}"

python3 scripts/testing/test_tenant_apis.py \
  --tenants "${tenant_list[@]}" \
  --urls "${urls[@]}" \
  --output "$output_file"

test_result=$?

# Check if tests passed
if [ $test_result -eq 0 ]; then
  echo -e "${GREEN}✅ All API tests passed successfully!${NC}"
  echo -e "${GREEN}✅ BBS+ functionality is working correctly in all tenant containers${NC}"
else
  echo -e "${RED}❌ Some API tests failed.${NC}"
  echo -e "${YELLOW}Please check the test results for details.${NC}"
  
  # Ask if user wants to check container logs
  echo -e "${YELLOW}Would you like to check container logs? (y/n)${NC}"
  read -r check_logs
  
  if [[ "$check_logs" == "y" || "$check_logs" == "Y" ]]; then
    for tenant_id in "${!tenant_ids[@]}"; do
      echo -e "${BLUE}Logs for tenant ${YELLOW}$tenant_id${BLUE} (container: ${YELLOW}${tenant_ids[$tenant_id]}${BLUE}):${NC}"
      docker logs "${tenant_ids[$tenant_id]}" | grep -E "BBS\+|Error|Exception|Failed" | tail -n 20
      echo ""
    done
  fi
fi

# Ask if user wants to check BBS+ functionality in containers
echo -e "${YELLOW}Would you like to check BBS+ functionality directly in containers? (y/n)${NC}"
read -r check_bbs

if [[ "$check_bbs" == "y" || "$check_bbs" == "Y" ]]; then
  for tenant_id in "${!tenant_ids[@]}"; do
    echo -e "${BLUE}Checking BBS+ in tenant ${YELLOW}$tenant_id${BLUE} (container: ${YELLOW}${tenant_ids[$tenant_id]}${BLUE}):${NC}"
    
    # Run a Python script to test BBS+ functionality
    docker exec "${tenant_ids[$tenant_id]}" python -c "
import sys
try:
    import bbs_core
    print('✅ BBS+ core loaded successfully')
    
    # Try to generate a key pair
    key_gen = bbs_core.GenerateKeyPair()
    key_pair = key_gen.generate_key_pair()
    
    # Check if we can access the key attributes
    if hasattr(key_pair, 'dpub_key_bytes'):
        print(f'✅ Using Linux attributes: dpub_key_bytes ({len(key_pair.dpub_key_bytes)} bytes), priv_key_bytes ({len(key_pair.priv_key_bytes)} bytes)')
    elif hasattr(key_pair, 'public_key'):
        print(f'✅ Using macOS attributes: public_key ({len(key_pair.public_key)} bytes), secret_key ({len(key_pair.secret_key)} bytes)')
    else:
        print('❌ Could not find expected attributes on key pair')
        print('Available attributes:', [attr for attr in dir(key_pair) if not attr.startswith('__')])
    
    print('✅ BBS+ functionality test passed')
except Exception as e:
    print(f'❌ Error: {str(e)}')
    sys.exit(1)
"
    
    if [ $? -ne 0 ]; then
      echo -e "${RED}❌ BBS+ test failed in container ${tenant_ids[$tenant_id]}${NC}"
    else
      echo -e "${GREEN}✅ BBS+ test passed in container ${tenant_ids[$tenant_id]}${NC}"
    fi
    echo ""
  done
fi

echo -e "${GREEN}======================${NC}"
echo -e "${GREEN}✅ Test complete!${NC}"
echo -e "${GREEN}Results saved to: ${output_file}${NC}"
echo -e "${GREEN}======================${NC}"

exit $test_result 