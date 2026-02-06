#!/bin/bash

# Runtime BBS+ Debugging Tool for Docker Containers
# Helps diagnose BBS+ issues in running containers without rebuilding
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
echo -e "${BLUE}│ StudentVC BBS+ Docker Runtime Debugger                │${NC}"
echo -e "${BLUE}│ Diagnoses BBS+ issues in running containers           │${NC}"
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
  echo -e "${RED}❌ Error: No running StudentVC containers found.${NC}"
  echo -e "${YELLOW}Please start the containers with 'make docker-run' first.${NC}"
  exit 1
fi

# Initialize arrays for tenant information
declare -A tenant_ids
declare -A tenant_names

# Get container information
while read -r container_id name ports; do
  tenant_id=$(echo "$name" | sed -n 's/.*studentvc-\(.*\)/\1/p')
  
  if [ -n "$tenant_id" ]; then
    tenant_ids["$tenant_id"]="$container_id"
    tenant_names["$container_id"]="$tenant_id"
    echo -e "${GREEN}✅ Found tenant ${BLUE}$tenant_id${GREEN} (container: ${BLUE}$container_id${GREEN})${NC}"
  fi
done < <(docker ps | grep -E 'studentvc-' | awk '{print $1, $2, $7}')

# Check if we found any tenants
if [ ${#tenant_ids[@]} -eq 0 ]; then
  echo -e "${RED}❌ Error: No StudentVC tenant containers found.${NC}"
  exit 1
fi

# Create a menu for selecting a container
echo -e "\n${CYAN}=== Available Containers ===${NC}"
options=()
i=1
for tenant_id in "${!tenant_ids[@]}"; do
  echo -e "${CYAN}$i)${NC} Tenant: ${MAGENTA}$tenant_id${NC} (Container: ${tenant_ids[$tenant_id]})"
  options+=("$tenant_id")
  ((i++))
done

# Ask user to select a container
echo -e "\n${YELLOW}Select a container to debug (1-${#tenant_ids[@]}):${NC}"
read -r selection

if ! [[ "$selection" =~ ^[0-9]+$ ]] || [ "$selection" -lt 1 ] || [ "$selection" -gt "${#tenant_ids[@]}" ]; then
  echo -e "${RED}❌ Invalid selection.${NC}"
  exit 1
fi

selected_tenant="${options[$((selection-1))]}"
selected_container="${tenant_ids[$selected_tenant]}"

echo -e "${GREEN}✅ Selected tenant: ${MAGENTA}$selected_tenant${GREEN} (Container: ${MAGENTA}$selected_container${GREEN})${NC}"

# Create a menu for debugging options
echo -e "\n${CYAN}=== Debugging Options ===${NC}"
echo -e "${CYAN}1)${NC} Check BBS+ core status"
echo -e "${CYAN}2)${NC} Test key generation"
echo -e "${CYAN}3)${NC} Inspect BBS+ module attributes"
echo -e "${CYAN}4)${NC} Check BBS+ file paths and permissions"
echo -e "${CYAN}5)${NC} View recent BBS+ related logs"
echo -e "${CYAN}6)${NC} Run custom Python code in container"
echo -e "${CYAN}7)${NC} Interactive Python shell"
echo -e "${CYAN}8)${NC} Interactive bash shell"
echo -e "${CYAN}9)${NC} Export BBS+ files from container"
echo -e "${CYAN}10)${NC} Import BBS+ files to container"

echo -e "\n${YELLOW}Select a debugging option (1-10):${NC}"
read -r debug_option

case $debug_option in
  1)
    echo -e "${BLUE}Checking BBS+ core status in container ${selected_container}...${NC}"
    docker exec "$selected_container" python -c "
import sys
try:
    import bbs_core
    print('✅ BBS+ core loaded successfully')
    
    # Get module info
    module_path = getattr(bbs_core, '__file__', 'Unknown')
    print(f'📁 BBS+ module path: {module_path}')
    
    # Check for .so file
    import os
    dir_path = os.path.dirname(module_path)
    so_files = [f for f in os.listdir(dir_path) if f.endswith('.so')]
    if so_files:
        print(f'📚 Found .so files: {so_files}')
    else:
        print('⚠️ No .so files found in module directory')
    
    print('✅ BBS+ core status check complete')
except Exception as e:
    print(f'❌ Error loading BBS+ core: {str(e)}')
    sys.exit(1)
"
    ;;
    
  2)
    echo -e "${BLUE}Testing BBS+ key generation in container ${selected_container}...${NC}"
    docker exec "$selected_container" python -c "
import sys
try:
    import bbs_core
    print('✅ BBS+ core loaded successfully')
    
    # Try to generate a key pair
    print('🔑 Generating key pair...')
    key_gen = bbs_core.GenerateKeyPair()
    key_pair = key_gen.generate_key_pair()
    print('✅ Key pair generated successfully')
    
    # Check available attributes
    print('🔍 Inspecting key pair attributes...')
    attrs = [attr for attr in dir(key_pair) if not attr.startswith('__')]
    print(f'📝 Available attributes: {attrs}')
    
    # Try to access key attributes using different naming conventions
    if hasattr(key_pair, 'dpub_key_bytes'):
        print(f'✅ Linux attributes: dpub_key_bytes ({len(key_pair.dpub_key_bytes)} bytes), priv_key_bytes ({len(key_pair.priv_key_bytes)} bytes)')
    elif hasattr(key_pair, 'public_key'):
        print(f'✅ macOS attributes: public_key ({len(key_pair.public_key)} bytes), secret_key ({len(key_pair.secret_key)} bytes)')
    else:
        print('⚠️ Could not find expected attributes on key pair')
        for attr in attrs:
            value = getattr(key_pair, attr)
            if isinstance(value, bytes):
                print(f'  - {attr}: {len(value)} bytes')
            else:
                print(f'  - {attr}: {type(value)}')
    
    print('✅ BBS+ key generation test complete')
except Exception as e:
    print(f'❌ Error during key generation: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    ;;
    
  3)
    echo -e "${BLUE}Inspecting BBS+ module attributes in container ${selected_container}...${NC}"
    docker exec "$selected_container" python -c "
import sys
try:
    import bbs_core
    print('✅ BBS+ core loaded successfully')
    
    # Get module info
    print('📝 BBS+ module info:')
    print(f'  - __file__: {getattr(bbs_core, \"__file__\", \"Unknown\")}')
    print(f'  - __name__: {getattr(bbs_core, \"__name__\", \"Unknown\")}')
    print(f'  - __package__: {getattr(bbs_core, \"__package__\", \"Unknown\")}')
    
    # List all attributes
    print('📝 BBS+ module attributes:')
    attrs = [attr for attr in dir(bbs_core) if not attr.startswith('__')]
    for attr in attrs:
        try:
            value = getattr(bbs_core, attr)
            print(f'  - {attr}: {type(value)}')
        except Exception as e:
            print(f'  - {attr}: Error accessing - {str(e)}')
    
    # Check for expected classes
    expected_classes = ['GenerateKeyPair', 'KeyPair', 'BBSSigner', 'BBSVerifier']
    print('🔍 Checking for expected classes:')
    for cls in expected_classes:
        if hasattr(bbs_core, cls):
            print(f'  ✅ {cls} found')
        else:
            print(f'  ❌ {cls} not found')
    
    print('✅ BBS+ module inspection complete')
except Exception as e:
    print(f'❌ Error inspecting BBS+ module: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"
    ;;
    
  4)
    echo -e "${BLUE}Checking BBS+ file paths and permissions in container ${selected_container}...${NC}"
    docker exec "$selected_container" bash -c "
echo '📁 Checking BBS+ files...'

# Check for bbs_core.py
if [ -f /app/bbs_core.py ]; then
  echo '✅ Found /app/bbs_core.py'
  ls -la /app/bbs_core.py
else
  echo '❌ /app/bbs_core.py not found'
fi

# Check for .so file
if [ -f /app/libuniffi_bbs_core.so ]; then
  echo '✅ Found /app/libuniffi_bbs_core.so'
  ls -la /app/libuniffi_bbs_core.so
else
  echo '❌ /app/libuniffi_bbs_core.so not found'
fi

# Check Python path
echo '🔍 Checking Python path...'
python -c 'import sys; print(\"\\n\".join(sys.path))'

# Check for other .so files
echo '🔍 Looking for other .so files in /app...'
find /app -name '*.so' -type f | xargs ls -la

echo '✅ File path check complete'
"
    ;;
    
  5)
    echo -e "${BLUE}Viewing recent BBS+ related logs in container ${selected_container}...${NC}"
    docker logs "$selected_container" 2>&1 | grep -E "BBS\+|bbs_core|uniffi|Error|Exception|Failed" | tail -n 50
    ;;
    
  6)
    echo -e "${BLUE}Running custom Python code in container ${selected_container}...${NC}"
    echo -e "${YELLOW}Enter Python code to run (end with EOF on a new line):${NC}"
    python_code=""
    while IFS= read -r line; do
      [[ "$line" == "EOF" ]] && break
      python_code+="$line"$'\n'
    done
    
    # Create a temporary file with the Python code
    temp_file=$(mktemp)
    echo "$python_code" > "$temp_file"
    
    # Copy the file to the container and run it
    docker cp "$temp_file" "$selected_container:/tmp/debug_script.py"
    docker exec "$selected_container" python /tmp/debug_script.py
    
    # Clean up
    rm "$temp_file"
    ;;
    
  7)
    echo -e "${BLUE}Starting interactive Python shell in container ${selected_container}...${NC}"
    echo -e "${YELLOW}Type 'exit()' to exit the shell.${NC}"
    docker exec -it "$selected_container" python
    ;;
    
  8)
    echo -e "${BLUE}Starting interactive bash shell in container ${selected_container}...${NC}"
    echo -e "${YELLOW}Type 'exit' to exit the shell.${NC}"
    docker exec -it "$selected_container" bash
    ;;
    
  9)
    echo -e "${BLUE}Exporting BBS+ files from container ${selected_container}...${NC}"
    
    # Create a directory for the exported files
    export_dir="bbs_export_${selected_tenant}_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$export_dir"
    
    # Export bbs_core.py
    docker cp "$selected_container:/app/bbs_core.py" "$export_dir/bbs_core.py" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Exported bbs_core.py${NC}"
    else
      echo -e "${RED}❌ Failed to export bbs_core.py${NC}"
    fi
    
    # Export libuniffi_bbs_core.so
    docker cp "$selected_container:/app/libuniffi_bbs_core.so" "$export_dir/libuniffi_bbs_core.so" 2>/dev/null
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Exported libuniffi_bbs_core.so${NC}"
    else
      echo -e "${RED}❌ Failed to export libuniffi_bbs_core.so${NC}"
    fi
    
    echo -e "${GREEN}✅ Files exported to ${export_dir}${NC}"
    ;;
    
  10)
    echo -e "${BLUE}Importing BBS+ files to container ${selected_container}...${NC}"
    
    # Check if we have Linux-compatible BBS+ files
    if [ -d "backend/bbs-core/linux-build" ]; then
      echo -e "${GREEN}✅ Found Linux-compatible BBS+ files in backend/bbs-core/linux-build${NC}"
      
      # Copy the files to the container
      docker cp "backend/bbs-core/linux-build/bbs_core.py" "$selected_container:/app/bbs_core.py"
      docker cp "backend/bbs-core/linux-build/libuniffi_bbs_core.so" "$selected_container:/app/libuniffi_bbs_core.so"
      
      echo -e "${GREEN}✅ Files imported to container${NC}"
      
      # Ask if user wants to restart the container
      echo -e "${YELLOW}Would you like to restart the container to apply the changes? (y/n)${NC}"
      read -r restart
      
      if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
        echo -e "${BLUE}Restarting container ${selected_container}...${NC}"
        docker restart "$selected_container"
        echo -e "${GREEN}✅ Container restarted${NC}"
      fi
    else
      echo -e "${RED}❌ Linux-compatible BBS+ files not found in backend/bbs-core/linux-build${NC}"
      echo -e "${YELLOW}Please run './test_bbs_linux_docker.sh' first to generate them${NC}"
      
      # Ask if user wants to specify custom files
      echo -e "${YELLOW}Would you like to specify custom BBS+ files to import? (y/n)${NC}"
      read -r custom_files
      
      if [[ "$custom_files" == "y" || "$custom_files" == "Y" ]]; then
        echo -e "${YELLOW}Enter path to bbs_core.py:${NC}"
        read -r bbs_core_path
        
        echo -e "${YELLOW}Enter path to libuniffi_bbs_core.so:${NC}"
        read -r so_path
        
        if [ -f "$bbs_core_path" ] && [ -f "$so_path" ]; then
          docker cp "$bbs_core_path" "$selected_container:/app/bbs_core.py"
          docker cp "$so_path" "$selected_container:/app/libuniffi_bbs_core.so"
          
          echo -e "${GREEN}✅ Custom files imported to container${NC}"
          
          # Ask if user wants to restart the container
          echo -e "${YELLOW}Would you like to restart the container to apply the changes? (y/n)${NC}"
          read -r restart
          
          if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
            echo -e "${BLUE}Restarting container ${selected_container}...${NC}"
            docker restart "$selected_container"
            echo -e "${GREEN}✅ Container restarted${NC}"
          fi
        else
          echo -e "${RED}❌ One or both files not found${NC}"
        fi
      fi
    fi
    ;;
    
  *)
    echo -e "${RED}❌ Invalid option.${NC}"
    exit 1
    ;;
esac

echo -e "${GREEN}======================${NC}"
echo -e "${GREEN}✅ Debugging complete!${NC}"
echo -e "${GREEN}======================${NC}" 