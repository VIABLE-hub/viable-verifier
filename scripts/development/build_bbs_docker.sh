#!/bin/bash

# Script to build and test BBS+ core in Docker
# This script verifies that the BBS+ UniFFI contract builds and works correctly on Linux
# Author: Patrick Herbke (via Cursor AI)

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}┌───────────────────────────────────────────────────────┐${NC}"
echo -e "${BLUE}│ StudentVC BBS+ Core Docker Builder                    │${NC}"
echo -e "${BLUE}│ Ensures UniFFI contract compatibility on Linux        │${NC}"
echo -e "${BLUE}└───────────────────────────────────────────────────────┘${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo -e "${RED}❌ Error: Docker is not running.${NC}"
  echo -e "${YELLOW}Please start Docker and try again.${NC}"
  exit 1
fi

echo -e "${YELLOW}🔍 Current directory: $(pwd)${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo -e "${YELLOW}🔍 Script directory: $SCRIPT_DIR${NC}"

# Navigate to project root (assumes script is in scripts/development/)
cd "$SCRIPT_DIR/../.." || exit 1
echo -e "${YELLOW}🔍 Project root: $(pwd)${NC}"

# Step 1: Build BBS test image
echo -e "\n${BLUE}Step 1: Building BBS+ test container...${NC}"
docker build --no-cache -t studentvc-bbs-test -f backend/Dockerfile --target bbs-test backend/
if [ $? -ne 0 ]; then
  echo -e "${RED}❌ Error: Failed to build BBS+ test image.${NC}"
  exit 1
fi
echo -e "${GREEN}✅ BBS+ test image built successfully.${NC}"

# Step 2: Run BBS test
echo -e "\n${BLUE}Step 2: Running BBS+ contract test...${NC}"
docker run --rm studentvc-bbs-test

# Step 3: Extract and save wheel file
echo -e "\n${BLUE}Step 3: Extracting BBS+ wheel from container...${NC}"
mkdir -p ./backend/wheels/
docker create --name temp-bbs-container studentvc-bbs-test
docker cp temp-bbs-container:/app/bbs_output/bbs_core-*.whl ./backend/wheels/
docker rm temp-bbs-container

echo -e "${GREEN}✅ BBS+ wheel extracted to ./backend/wheels/${NC}"

# Show wheel file
ls -la ./backend/wheels/

echo -e "\n${GREEN}✅ BBS+ Docker build and test completed successfully!${NC}"
echo -e "${BLUE}───────────────────────────────────────────────────────${NC}"
echo -e "${YELLOW}You can now run:${NC}"
echo -e "   make docker-build    ${GREEN}# Build all tenant images${NC}"
echo -e "   make docker-run      ${GREEN}# Start all tenants${NC}"
echo -e "${BLUE}───────────────────────────────────────────────────────${NC}" 