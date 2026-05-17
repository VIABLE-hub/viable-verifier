#!/bin/bash

# Hot-patching Tool for BBS+ in Docker Containers
# Automatically fixes BBS+ issues in running containers without rebuilding
# Author: Patrick Herbke (via Cursor AI)

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}┌───────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ VIABLE Credentials BBS+ Docker Hot-Patching Tool               │${NC}"
echo -e "${BLUE}│ Automatically fixes BBS+ issues in running containers │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────────────┘${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}❌ Error: Docker is not running.${NC}"
  echo -e "${YELLOW}Please start Docker and try again.${NC}"
  exit 1
fi

# Check for Linux-compatible BBS+ files
if [ ! -d "backend/bbs-core/linux-build" ]; then
  echo -e "${YELLOW}⚠️ Linux-compatible BBS+ files not found in backend/bbs-core/linux-build${NC}"
  echo -e "${YELLOW}Generating Linux-compatible BBS+ files...${NC}"
  
  # Check if test_bbs_linux_docker.sh exists
  if [ -f "test_bbs_linux_docker.sh" ]; then
    ./test_bbs_linux_docker.sh
    
    if [ ! -d "backend/bbs-core/linux-build" ]; then
      echo -e "${RED}❌ Failed to generate Linux-compatible BBS+ files.${NC}"
      exit 1
    fi
  else
    echo -e "${RED}❌ test_bbs_linux_docker.sh not found.${NC}"
    echo -e "${YELLOW}Please run this script from the project root directory.${NC}"
    exit 1
  fi
fi

# Check if containers are running
echo -e "${BLUE}Checking for running VIABLE Credentials containers...${NC}"
containers=$(docker ps | grep -E 'viable-credentials-' | awk '{print $1}')

if [ -z "$containers" ]; then
  echo -e "${RED}❌ Error: No running VIABLE Credentials containers found.${NC}"
  echo -e "${YELLOW}Please start the containers with 'make docker-run' first.${NC}"
  exit 1
fi

# Get container information
declare -A tenant_ids
declare -A tenant_names
container_count=0

while read -r container_id name ports; do
  tenant_id=$(echo "$name" | sed -n 's/.*viable-credentials-\(.*\)/\1/p')
  
  if [ -n "$tenant_id" ]; then
    tenant_ids["$tenant_id"]="$container_id"
    tenant_names["$container_id"]="$tenant_id"
    echo -e "${GREEN}✅ Found tenant ${BLUE}$tenant_id${GREEN} (container: ${BLUE}$container_id${GREEN})${NC}"
    ((container_count++))
  fi
done < <(docker ps | grep -E 'viable-credentials-' | awk '{print $1, $2, $7}')

echo -e "${GREEN}✅ Found ${container_count} VIABLE Credentials containers${NC}"

# Function to patch a container
patch_container() {
  local container_id=$1
  local tenant_id=$2
  
  echo -e "${BLUE}Patching container ${MAGENTA}$container_id${BLUE} (tenant: ${MAGENTA}$tenant_id${BLUE})...${NC}"
  
  # Copy the Linux-compatible BBS+ files to the container
  echo -e "${YELLOW}Copying Linux-compatible BBS+ files...${NC}"
  docker cp "backend/bbs-core/linux-build/bbs_core.py" "$container_id:/app/bbs_core.py"
  docker cp "backend/bbs-core/linux-build/libuniffi_bbs_core.so" "$container_id:/app/libuniffi_bbs_core.so"
  
  # Verify the files were copied
  echo -e "${YELLOW}Verifying files...${NC}"
  docker exec "$container_id" ls -la /app/bbs_core.py /app/libuniffi_bbs_core.so
  
  # Test BBS+ functionality
  echo -e "${YELLOW}Testing BBS+ functionality...${NC}"
  docker exec "$container_id" python -c "
import sys
try:
    import bbs_core
    print('✅ BBS+ core loaded successfully')
    
    # Try to generate a key pair
    key_gen = bbs_core.GenerateKeyPair()
    key_pair = key_gen.generate_key_pair()
    print('✅ Key pair generated successfully')
    
    # Check available attributes
    attrs = [attr for attr in dir(key_pair) if not attr.startswith('__')]
    
    # Try to access key attributes
    if hasattr(key_pair, 'dpub_key_bytes'):
        print(f'✅ Linux attributes confirmed: dpub_key_bytes ({len(key_pair.dpub_key_bytes)} bytes), priv_key_bytes ({len(key_pair.priv_key_bytes)} bytes)')
    elif hasattr(key_pair, 'public_key'):
        print(f'✅ macOS attributes detected: public_key ({len(key_pair.public_key)} bytes), secret_key ({len(key_pair.secret_key)} bytes)')
    else:
        print('⚠️ Could not find expected attributes on key pair')
        sys.exit(1)
    
    print('✅ BBS+ functionality test passed')
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
  
  # Check if the test was successful
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container ${MAGENTA}$container_id${GREEN} patched successfully${NC}"
    return 0
  else
    echo -e "${RED}❌ Failed to patch container ${MAGENTA}$container_id${RED}${NC}"
    return 1
  fi
}

# Function to check if container needs patching
check_container() {
  local container_id=$1
  local tenant_id=$2
  
  echo -e "${BLUE}Checking container ${MAGENTA}$container_id${BLUE} (tenant: ${MAGENTA}$tenant_id${BLUE})...${NC}"
  
  # Check if BBS+ is working correctly
  docker exec "$container_id" python -c "
import sys
try:
    import bbs_core
    
    # Try to generate a key pair
    key_gen = bbs_core.GenerateKeyPair()
    key_pair = key_gen.generate_key_pair()
    
    # Check for Linux attributes
    if hasattr(key_pair, 'dpub_key_bytes'):
        print('✅ BBS+ working correctly with Linux attributes')
        sys.exit(0)
    elif hasattr(key_pair, 'public_key'):
        print('⚠️ BBS+ using macOS attributes, needs patching')
        sys.exit(1)
    else:
        print('⚠️ BBS+ missing expected attributes, needs patching')
        sys.exit(1)
except Exception as e:
    print(f'❌ BBS+ error: {str(e)}')
    sys.exit(1)
" >/dev/null 2>&1
  
  return $?
}

# Ask if user wants to patch all containers or select specific ones
echo -e "\n${YELLOW}Do you want to patch all containers or select specific ones?${NC}"
echo -e "${CYAN}1)${NC} Patch all containers"
echo -e "${CYAN}2)${NC} Select specific containers"

read -r selection

case $selection in
  1)
    echo -e "${BLUE}Patching all containers...${NC}"
    success_count=0
    failure_count=0
    
    for tenant_id in "${!tenant_ids[@]}"; do
      container_id="${tenant_ids[$tenant_id]}"
      
      # Check if container needs patching
      check_container "$container_id" "$tenant_id"
      if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Container ${MAGENTA}$container_id${GREEN} (tenant: ${MAGENTA}$tenant_id${GREEN}) already has correct BBS+ files${NC}"
        ((success_count++))
        continue
      fi
      
      # Patch container
      patch_container "$container_id" "$tenant_id"
      if [ $? -eq 0 ]; then
        ((success_count++))
      else
        ((failure_count++))
      fi
    done
    
    echo -e "\n${BLUE}Patching summary:${NC}"
    echo -e "${GREEN}✅ Successfully patched: $success_count containers${NC}"
    echo -e "${RED}❌ Failed to patch: $failure_count containers${NC}"
    ;;
    
  2)
    # Create a menu for selecting containers
    echo -e "\n${CYAN}=== Available Containers ===${NC}"
    options=()
    i=1
    for tenant_id in "${!tenant_ids[@]}"; do
      container_id="${tenant_ids[$tenant_id]}"
      
      # Check if container needs patching
      check_container "$container_id" "$tenant_id"
      needs_patching=$?
      
      if [ $needs_patching -eq 0 ]; then
        status="${GREEN}[OK]${NC}"
      else
        status="${YELLOW}[NEEDS PATCHING]${NC}"
      fi
      
      echo -e "${CYAN}$i)${NC} Tenant: ${MAGENTA}$tenant_id${NC} (Container: ${tenant_ids[$tenant_id]}) $status"
      options+=("$tenant_id")
      ((i++))
    done
    
    # Ask user to select a container
    echo -e "\n${YELLOW}Select a container to patch (1-${#tenant_ids[@]}):${NC}"
    read -r container_selection
    
    if ! [[ "$container_selection" =~ ^[0-9]+$ ]] || [ "$container_selection" -lt 1 ] || [ "$container_selection" -gt "${#tenant_ids[@]}" ]; then
      echo -e "${RED}❌ Invalid selection.${NC}"
      exit 1
    fi
    
    selected_tenant="${options[$((container_selection-1))]}"
    selected_container="${tenant_ids[$selected_tenant]}"
    
    echo -e "${GREEN}✅ Selected tenant: ${MAGENTA}$selected_tenant${GREEN} (Container: ${MAGENTA}$selected_container${GREEN})${NC}"
    
    # Check if container needs patching
    check_container "$selected_container" "$selected_tenant"
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Container ${MAGENTA}$selected_container${GREEN} already has correct BBS+ files${NC}"
      echo -e "${YELLOW}Do you want to force patch it anyway? (y/n)${NC}"
      read -r force_patch
      
      if [[ "$force_patch" != "y" && "$force_patch" != "Y" ]]; then
        echo -e "${BLUE}Skipping container ${MAGENTA}$selected_container${BLUE}${NC}"
        exit 0
      fi
    fi
    
    # Patch container
    patch_container "$selected_container" "$selected_tenant"
    ;;
    
  *)
    echo -e "${RED}❌ Invalid selection.${NC}"
    exit 1
    ;;
esac

# Ask if user wants to restart containers
echo -e "\n${YELLOW}Do you want to restart the patched containers? (y/n)${NC}"
read -r restart

if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
  if [ "$selection" -eq 1 ]; then
    echo -e "${BLUE}Restarting all containers...${NC}"
    for tenant_id in "${!tenant_ids[@]}"; do
      container_id="${tenant_ids[$tenant_id]}"
      echo -e "${BLUE}Restarting container ${MAGENTA}$container_id${BLUE} (tenant: ${MAGENTA}$tenant_id${BLUE})...${NC}"
      docker restart "$container_id"
    done
  else
    echo -e "${BLUE}Restarting container ${MAGENTA}$selected_container${BLUE} (tenant: ${MAGENTA}$selected_tenant${BLUE})...${NC}"
    docker restart "$selected_container"
  fi
  
  echo -e "${GREEN}✅ Containers restarted${NC}"
fi

echo -e "${GREEN}======================${NC}"
echo -e "${GREEN}✅ Hot-patching complete!${NC}"
echo -e "${GREEN}======================${NC}" 