#!/bin/bash

# Script to update an existing Docker container with Linux-compatible BBS+ files
# Author: Patrick Herbke (via Cursor AI)

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}┌───────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ StudentVC BBS+ Docker Container Updater               │${NC}"
echo -e "${BLUE}│ Updates existing containers with Linux BBS+ bindings  │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────────────┘${NC}"

# Check if Linux-compatible BBS+ files exist
if [ ! -d "backend/bbs-core/linux-build" ]; then
  echo -e "${RED}❌ Linux-compatible BBS+ files not found at backend/bbs-core/linux-build${NC}"
  echo -e "${YELLOW}Please run './test_bbs_linux_docker.sh' first to generate them${NC}"
  exit 1
fi

echo -e "${BLUE}Finding running StudentVC containers...${NC}"
containers=$(docker ps | grep -E 'studentvc-|bbs-test' | awk '{print $1}')

if [ -z "$containers" ]; then
  echo -e "${YELLOW}No running StudentVC containers found.${NC}"
  echo -e "${YELLOW}Would you like to update the Docker images instead? (y/n)${NC}"
  read -r update_images
  
  if [[ "$update_images" == "y" || "$update_images" == "Y" ]]; then
    echo -e "${BLUE}Finding StudentVC Docker images...${NC}"
    images=$(docker images | grep -E 'studentvc-|bbs-test' | awk '{print $1}')
    
    if [ -z "$images" ]; then
      echo -e "${RED}No StudentVC Docker images found.${NC}"
      exit 1
    fi
    
    echo -e "${BLUE}Found the following Docker images:${NC}"
    echo "$images"
    
    echo -e "${YELLOW}This will create new Docker images with the Linux-compatible BBS+ files.${NC}"
    echo -e "${YELLOW}Continue? (y/n)${NC}"
    read -r continue
    
    if [[ "$continue" != "y" && "$continue" != "Y" ]]; then
      echo -e "${RED}Operation cancelled${NC}"
      exit 0
    fi
    
    echo -e "${BLUE}Building Docker images with Linux-compatible BBS+ files...${NC}"
    echo -e "${GREEN}✅ Use 'make docker-build' to build the images${NC}"
    exit 0
  else
    echo -e "${RED}Operation cancelled${NC}"
    exit 0
  fi
fi

echo -e "${BLUE}Found the following containers:${NC}"
docker ps | grep -E 'studentvc-|bbs-test'

echo -e "${YELLOW}This will copy the Linux-compatible BBS+ files to the containers.${NC}"
echo -e "${YELLOW}Continue? (y/n)${NC}"
read -r continue

if [[ "$continue" != "y" && "$continue" != "Y" ]]; then
  echo -e "${RED}Operation cancelled${NC}"
  exit 0
fi

# For each container, copy the Linux-compatible BBS+ files
for container in $containers; do
  echo -e "${BLUE}Updating container ${container}...${NC}"
  
  # Copy the Linux-compatible BBS+ files to the container
  docker cp backend/bbs-core/linux-build/libuniffi_bbs_core.so "${container}:/app/"
  docker cp backend/bbs-core/linux-build/bbs_core.py "${container}:/app/"
  
  echo -e "${GREEN}✅ Files copied to container ${container}${NC}"
  
  # Restart the container's Python process to load the new files
  echo -e "${YELLOW}Would you like to restart the container to apply the changes? (y/n)${NC}"
  read -r restart
  
  if [[ "$restart" == "y" || "$restart" == "Y" ]]; then
    echo -e "${BLUE}Restarting container ${container}...${NC}"
    docker restart "${container}"
    echo -e "${GREEN}✅ Container ${container} restarted${NC}"
  fi
done

echo -e "${GREEN}======================${NC}"
echo -e "${GREEN}✅ Update complete!${NC}"
echo -e "${GREEN}======================${NC}" 