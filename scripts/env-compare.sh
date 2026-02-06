#!/bin/bash

# Environment Files Comparison Script
# Compares variables across different environment file templates

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Environment Files Comparison${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to extract variable names from file
get_variables() {
    local file="$1"
    if [ -f "$file" ]; then
        grep -E "^[A-Z_]+=" "$file" | cut -d'=' -f1 | sort | uniq
    fi
}

# Function to count variables
count_variables() {
    local file="$1"
    if [ -f "$file" ]; then
        grep -cE "^[A-Z_]+=" "$file" || echo "0"
    else
        echo "0"
    fi
}

# Environment files to compare
ENV_EXAMPLE="$PROJECT_ROOT/env.example"
DEPLOYMENT_ENV="$PROJECT_ROOT/deployment.env"
PRODUCTION_TEMPLATE="$PROJECT_ROOT/config/production.env.template"
DOCKER_ENV="$PROJECT_ROOT/deploy/configs/docker.env"
ACTUAL_ENV="$PROJECT_ROOT/.env"

echo -e "${MAGENTA}📊 Environment Files Overview${NC}"
echo ""

# Check which files exist
echo -e "${BLUE}Available Files:${NC}"
[ -f "$ENV_EXAMPLE" ] && echo -e "${GREEN}✓ env.example ($(count_variables "$ENV_EXAMPLE") vars)${NC}" || echo -e "${RED}✗ env.example${NC}"
[ -f "$DEPLOYMENT_ENV" ] && echo -e "${GREEN}✓ deployment.env ($(count_variables "$DEPLOYMENT_ENV") vars)${NC}" || echo -e "${RED}✗ deployment.env${NC}"
[ -f "$PRODUCTION_TEMPLATE" ] && echo -e "${GREEN}✓ production.env.template ($(count_variables "$PRODUCTION_TEMPLATE") vars)${NC}" || echo -e "${RED}✗ production.env.template${NC}"
[ -f "$DOCKER_ENV" ] && echo -e "${GREEN}✓ docker.env ($(count_variables "$DOCKER_ENV") vars)${NC}" || echo -e "${RED}✗ docker.env${NC}"
[ -f "$ACTUAL_ENV" ] && echo -e "${GREEN}✓ .env ($(count_variables "$ACTUAL_ENV") vars)${NC}" || echo -e "${YELLOW}⚠️  .env (file exists but can't read - this is normal)${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# Compare env.example with actual .env (if readable)
if [ -f "$ACTUAL_ENV" ] && [ -r "$ACTUAL_ENV" ]; then
    echo -e "${MAGENTA}📋 Comparing .env with env.example${NC}"
    echo ""
    
    EXAMPLE_VARS=$(get_variables "$ENV_EXAMPLE")
    ACTUAL_VARS=$(get_variables "$ACTUAL_ENV")
    
    # Variables in example but not in .env
    echo -e "${YELLOW}Variables in env.example but NOT in .env:${NC}"
    comm -23 <(echo "$EXAMPLE_VARS") <(echo "$ACTUAL_VARS") | head -20
    MISSING_COUNT=$(comm -23 <(echo "$EXAMPLE_VARS") <(echo "$ACTUAL_VARS") | wc -l)
    echo -e "${YELLOW}... ($MISSING_COUNT total)${NC}"
    echo ""
    
    # Variables in .env but not in example
    echo -e "${YELLOW}Variables in .env but NOT in env.example (custom):${NC}"
    comm -13 <(echo "$EXAMPLE_VARS") <(echo "$ACTUAL_VARS") | head -10
    EXTRA_COUNT=$(comm -13 <(echo "$EXAMPLE_VARS") <(echo "$ACTUAL_VARS") | wc -l)
    echo -e "${YELLOW}... ($EXTRA_COUNT total)${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Cannot read .env file (this is normal for security)${NC}"
    echo -e "${YELLOW}   Use './scripts/env-check.sh' for environment validation${NC}"
    echo ""
fi

# Compare different templates
echo -e "${BLUE}========================================${NC}"
echo -e "${MAGENTA}📊 Variable Coverage by File${NC}"
echo ""

# Get unique variables across all files
ALL_VARS=""
[ -f "$ENV_EXAMPLE" ] && ALL_VARS="$ALL_VARS $(get_variables "$ENV_EXAMPLE")"
[ -f "$DEPLOYMENT_ENV" ] && ALL_VARS="$ALL_VARS $(get_variables "$DEPLOYMENT_ENV")"
[ -f "$PRODUCTION_TEMPLATE" ] && ALL_VARS="$ALL_VARS $(get_variables "$PRODUCTION_TEMPLATE")"
[ -f "$DOCKER_ENV" ] && ALL_VARS="$ALL_VARS $(get_variables "$DOCKER_ENV")"

UNIQUE_VARS=$(echo "$ALL_VARS" | tr ' ' '\n' | sort | uniq)
TOTAL_UNIQUE=$(echo "$UNIQUE_VARS" | wc -l)

echo -e "${BLUE}Total Unique Variables Across All Files: $TOTAL_UNIQUE${NC}"
echo ""

# Key variable categories
echo -e "${MAGENTA}🔑 Critical Variables Coverage${NC}"
echo ""

check_var_in_files() {
    local var="$1"
    local status=""
    
    [ -f "$ENV_EXAMPLE" ] && grep -q "^${var}=" "$ENV_EXAMPLE" 2>/dev/null && status="${status}${GREEN}E${NC} " || status="${status}${RED}-${NC} "
    [ -f "$DEPLOYMENT_ENV" ] && grep -q "^${var}=" "$DEPLOYMENT_ENV" 2>/dev/null && status="${status}${GREEN}D${NC} " || status="${status}${RED}-${NC} "
    [ -f "$PRODUCTION_TEMPLATE" ] && grep -q "^${var}=" "$PRODUCTION_TEMPLATE" 2>/dev/null && status="${status}${GREEN}P${NC} " || status="${status}${RED}-${NC} "
    [ -f "$DOCKER_ENV" ] && grep -q "^${var}=" "$DOCKER_ENV" 2>/dev/null && status="${status}${GREEN}C${NC}" || status="${status}${RED}-${NC}"
    
    echo -e "$status"
}

echo -e "${BLUE}Legend: [E]nv.example [D]eployment [P]roduction [C]ontainer${NC}"
echo ""

CRITICAL_VARS=(
    "FLASK_ENV"
    "FLASK_SECRET_KEY"
    "SECRET_KEY"
    "SERVER_PORT"
    "SERVER_URL"
    "DATABASE_URL"
    "TENANT_ID"
    "USE_HTTPS"
    "NGROK_URL"
    "DOCKER_MODE"
)

for var in "${CRITICAL_VARS[@]}"; do
    status=$(check_var_in_files "$var")
    printf "%-25s %b\n" "$var" "$status"
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo ""

# File-specific unique variables
echo -e "${MAGENTA}📝 File-Specific Variables${NC}"
echo ""

if [ -f "$DOCKER_ENV" ] && [ -f "$ENV_EXAMPLE" ]; then
    echo -e "${BLUE}Docker-specific variables:${NC}"
    DOCKER_VARS=$(get_variables "$DOCKER_ENV")
    EXAMPLE_VARS=$(get_variables "$ENV_EXAMPLE")
    comm -23 <(echo "$DOCKER_VARS") <(echo "$EXAMPLE_VARS") | head -10
    echo ""
fi

if [ -f "$DEPLOYMENT_ENV" ] && [ -f "$ENV_EXAMPLE" ]; then
    echo -e "${BLUE}Deployment-specific variables:${NC}"
    DEPLOY_VARS=$(get_variables "$DEPLOYMENT_ENV")
    EXAMPLE_VARS=$(get_variables "$ENV_EXAMPLE")
    comm -23 <(echo "$DEPLOY_VARS") <(echo "$EXAMPLE_VARS") | head -10
    echo ""
fi

# Recommendations
echo -e "${BLUE}========================================${NC}"
echo -e "${MAGENTA}💡 Recommendations${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -f "$ACTUAL_ENV" ]; then
    echo -e "${RED}❌ No .env file found!${NC}"
    echo -e "${YELLOW}   Create with: cp env.example .env${NC}"
    echo ""
fi

echo -e "${GREEN}✓ Use env.example as your primary template (most complete)${NC}"
echo -e "${GREEN}✓ Use deployment.env for multi-tenant production${NC}"
echo -e "${GREEN}✓ Use docker.env for container-based development${NC}"
echo -e "${GREEN}✓ Use production.env.template for single-tenant production${NC}"
echo ""

echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "  1. Run: ${BLUE}./scripts/env-check.sh${NC} to validate your .env"
echo -e "  2. Compare your setup with appropriate template above"
echo -e "  3. Ensure all CRITICAL variables are configured"
echo -e "  4. Generate secure keys for production"
echo ""

exit 0

