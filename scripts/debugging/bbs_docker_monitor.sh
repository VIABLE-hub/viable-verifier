#!/bin/bash

# BBS+ Docker Monitoring Tool
# Continuously monitors BBS+ health in Docker containers
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
CHECK_INTERVAL=60  # seconds between checks
LOG_FILE="bbs_monitor_$(date +%Y%m%d_%H%M%S).log"
ALERT_THRESHOLD=3  # number of consecutive failures before alerting

echo -e "${BLUE}┌───────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ VIABLE Credentials BBS+ Docker Monitor                         │${NC}"
echo -e "${BLUE}│ Continuously monitors BBS+ health in Docker containers │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────────────┘${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}❌ Error: Docker is not running.${NC}"
  echo -e "${YELLOW}Please start Docker and try again.${NC}"
  exit 1
fi

# Function to log messages to console and file
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
    "ALERT")
      echo -e "${MAGENTA}[ALERT]${NC} $timestamp - $message"
      ;;
    *)
      echo -e "$timestamp - $message"
      ;;
  esac
  
  echo "[$level] $timestamp - $message" >> "$LOG_FILE"
}

# Function to check BBS+ health in a container
check_bbs_health() {
  local container_id=$1
  local tenant_id=$2
  
  # Check if BBS+ is working correctly
  docker exec "$container_id" python -c "
import sys
try:
    import bbs_core
    
    # Try to generate a key pair
    key_gen = bbs_core.GenerateKeyPair()
    key_pair = key_gen.generate_key_pair()
    
    # Check for attributes
    if hasattr(key_pair, 'dpub_key_bytes') or hasattr(key_pair, 'public_key'):
        # Try to access the attributes
        if hasattr(key_pair, 'dpub_key_bytes'):
            dpub_key = key_pair.dpub_key_bytes
        else:
            public_key = key_pair.public_key
            
        print('BBS+ working correctly')
        sys.exit(0)
    else:
        print('BBS+ missing expected attributes')
        sys.exit(1)
except ImportError as e:
    print(f'BBS+ import error: {str(e)}')
    sys.exit(2)
except Exception as e:
    print(f'BBS+ error: {str(e)}')
    sys.exit(3)
" >/dev/null 2>&1
  
  return $?
}

# Function to get container information
get_containers() {
  # Initialize arrays for tenant information
  declare -A tenant_ids
  declare -A tenant_names
  
  # Get container information
  while read -r container_id name ports; do
    tenant_id=$(echo "$name" | sed -n 's/.*viable-credentials-\(.*\)/\1/p')
    
    if [ -n "$tenant_id" ]; then
      tenant_ids["$tenant_id"]="$container_id"
      tenant_names["$container_id"]="$tenant_id"
    fi
  done < <(docker ps | grep -E 'viable-credentials-' | awk '{print $1, $2, $7}')
  
  # Return the arrays as a string
  for tenant_id in "${!tenant_ids[@]}"; do
    echo "$tenant_id:${tenant_ids[$tenant_id]}"
  done
}

# Function to send an alert
send_alert() {
  local tenant_id=$1
  local container_id=$2
  local error_code=$3
  local error_message=""
  
  case $error_code in
    1)
      error_message="BBS+ missing expected attributes"
      ;;
    2)
      error_message="BBS+ import error"
      ;;
    3)
      error_message="BBS+ general error"
      ;;
    *)
      error_message="Unknown error"
      ;;
  esac
  
  log "ALERT" "BBS+ issue detected in container $container_id (tenant: $tenant_id): $error_message"
  
  # Display alert message
  echo -e "\n${RED}┌───────────────────────────────────────────────────────┐${NC}"
  echo -e "${RED}│ 🚨 BBS+ ALERT: Issue detected in container              │${NC}"
  echo -e "${RED}│ Tenant: $tenant_id${NC}"
  echo -e "${RED}│ Container: $container_id${NC}"
  echo -e "${RED}│ Error: $error_message${NC}"
  echo -e "${RED}└───────────────────────────────────────────────────────┘${NC}"
  echo -e "${YELLOW}Recommended action: Run 'make hot-patch-bbs' to fix the issue${NC}\n"
  
  # Send desktop notification if available
  if command -v notify-send &> /dev/null; then
    notify-send "BBS+ Alert" "Issue detected in container $container_id (tenant: $tenant_id): $error_message"
  elif command -v osascript &> /dev/null; then
    osascript -e "display notification \"Issue detected in container $container_id (tenant: $tenant_id): $error_message\" with title \"BBS+ Alert\""
  fi
}

# Initialize failure counters
declare -A failure_counters

# Main monitoring loop
log "INFO" "Starting BBS+ monitoring with check interval of $CHECK_INTERVAL seconds"
log "INFO" "Logging to $LOG_FILE"

while true; do
  # Get containers
  containers=$(get_containers)
  
  if [ -z "$containers" ]; then
    log "WARN" "No VIABLE Credentials containers found"
    sleep $CHECK_INTERVAL
    continue
  fi
  
  # Check each container
  while IFS=: read -r tenant_id container_id; do
    log "INFO" "Checking BBS+ health in container $container_id (tenant: $tenant_id)"
    
    # Check BBS+ health
    check_bbs_health "$container_id" "$tenant_id"
    result=$?
    
    # Handle the result
    if [ $result -eq 0 ]; then
      log "INFO" "BBS+ health check passed for container $container_id (tenant: $tenant_id)"
      failure_counters["$container_id"]=0
    else
      # Increment failure counter
      if [ -z "${failure_counters[$container_id]}" ]; then
        failure_counters["$container_id"]=1
      else
        failure_counters["$container_id"]=$((failure_counters["$container_id"] + 1))
      fi
      
      # Log the failure
      log "WARN" "BBS+ health check failed for container $container_id (tenant: $tenant_id) - Failure count: ${failure_counters[$container_id]}"
      
      # Send alert if threshold reached
      if [ "${failure_counters[$container_id]}" -ge $ALERT_THRESHOLD ]; then
        send_alert "$tenant_id" "$container_id" $result
      fi
    fi
  done <<< "$containers"
  
  # Wait for next check
  log "INFO" "Sleeping for $CHECK_INTERVAL seconds until next check"
  sleep $CHECK_INTERVAL
done 