#!/bin/bash

# Environment Configuration Check Script for StudentVC
# This script validates the .env file against env.example template

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/env.example"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}StudentVC Environment Configuration Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}📝 Creating .env from env.example...${NC}"
    
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo -e "${GREEN}✓ Created .env file. Please edit it with your actual values.${NC}"
        exit 1
    else
        echo -e "${RED}❌ Error: env.example not found at $ENV_EXAMPLE${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ .env file found${NC}"
echo ""

# Function to check if variable is set in .env
check_env_var() {
    local var_name="$1"
    local required="$2"
    local current_value=$(grep "^${var_name}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    local example_value=$(grep "^${var_name}=" "$ENV_EXAMPLE" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    
    if [ -z "$current_value" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ MISSING (Required): $var_name${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  MISSING (Optional): $var_name${NC}"
            return 2
        fi
    elif [ "$current_value" = "$example_value" ] || [[ "$current_value" == *"your-"* ]] || [[ "$current_value" == *"here"* ]]; then
        if [ "$required" = "true" ]; then
            echo -e "${YELLOW}⚠️  NOT CONFIGURED: $var_name (still has template value)${NC}"
            return 3
        else
            echo -e "${YELLOW}⚠️  TEMPLATE VALUE: $var_name (optional)${NC}"
            return 4
        fi
    else
        echo -e "${GREEN}✓ CONFIGURED: $var_name${NC}"
        return 0
    fi
}

# Function to load .env file and check for required variables
echo -e "${BLUE}Checking critical configuration variables...${NC}"
echo ""

# Critical Flask settings
echo -e "${BLUE}--- Flask Application Settings ---${NC}"
check_env_var "FLASK_ENV" "true"
check_env_var "FLASK_SECRET_KEY" "true"
check_env_var "FLASK_DEBUG" "false"
check_env_var "FLASK_APP" "true"
echo ""

# Server configuration
echo -e "${BLUE}--- Server Configuration ---${NC}"
check_env_var "SERVER_HOST" "true"
check_env_var "SERVER_PORT" "true"
check_env_var "SERVER_URL" "true"
check_env_var "USE_HTTPS" "false"
echo ""

# Database configuration
echo -e "${BLUE}--- Database Configuration ---${NC}"
check_env_var "DATABASE_URL" "true"
echo ""

# BBS+ Core and Crypto
echo -e "${BLUE}--- Cryptographic Settings ---${NC}"
check_env_var "BBS_CORE_PATH" "false"
check_env_var "KEY_STORAGE_PATH" "true"
check_env_var "ISSUER_PRIVATE_KEY_PATH" "false"
echo ""

# NGROK Configuration
echo -e "${BLUE}--- NGROK Configuration ---${NC}"
check_env_var "NGROK_ENABLED" "false"
check_env_var "NGROK_URL" "false"
echo ""

# Tenant Configuration
echo ""

# Authentication
echo -e "${BLUE}--- Authentication Settings ---${NC}"
check_env_var "ENABLE_AUTH" "false"
check_env_var "ACCESS_PASSWORD" "false"
echo ""

# Check for dangerous values
echo ""
echo -e "${BLUE}Checking for security issues...${NC}"
echo ""

SECURITY_ISSUES=0

# Check for default secret key
if grep -q "FLASK_SECRET_KEY=your-secret-key-here" "$ENV_FILE" 2>/dev/null; then
    echo -e "${RED}🔒 SECURITY ISSUE: FLASK_SECRET_KEY is still set to default value!${NC}"
    echo -e "${YELLOW}   Generate a secure key with: python -c \"import secrets; print(secrets.token_hex(32))\"${NC}"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check if debug is enabled
if grep -q "FLASK_DEBUG=True" "$ENV_FILE" 2>/dev/null && grep -q "FLASK_ENV=production" "$ENV_FILE" 2>/dev/null; then
    echo -e "${RED}🔒 SECURITY ISSUE: DEBUG mode is enabled in production!${NC}"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

# Check for localhost in production
if grep -q "FLASK_ENV=production" "$ENV_FILE" 2>/dev/null && grep -q "SERVER_URL=.*localhost" "$ENV_FILE" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: SERVER_URL uses localhost in production environment${NC}"
    SECURITY_ISSUES=$((SECURITY_ISSUES + 1))
fi

if [ $SECURITY_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ No obvious security issues detected${NC}"
fi

# Check if required directories exist
echo ""
echo -e "${BLUE}Checking required directories...${NC}"
echo ""

check_directory() {
    local dir="$1"
    local full_path="$PROJECT_ROOT/$dir"
    
    if [ -d "$full_path" ]; then
        echo -e "${GREEN}✓ Directory exists: $dir${NC}"
    else
        echo -e "${YELLOW}⚠️  Directory missing: $dir (will be created if needed)${NC}"
    fi
}

check_directory "backend/instance"
check_directory "backend/instance/keys"
check_directory "backend/logs"

# Check BBS Core library
echo ""
echo -e "${BLUE}Checking BBS+ Core library...${NC}"
echo ""

BBS_CORE_FILES=(
    "backend/libbbs_core.dylib"
    "backend/libuniffi_bbs_core.dylib"
    "backend/libuniffi_bbs_core.so"
)

BBS_FOUND=false
for file in "${BBS_CORE_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$file" ]; then
        echo -e "${GREEN}✓ Found: $file${NC}"
        BBS_FOUND=true
    fi
done

if [ "$BBS_FOUND" = false ]; then
    echo -e "${YELLOW}⚠️  WARNING: No BBS+ Core library files found${NC}"
    echo -e "${YELLOW}   Build BBS Core with: make build-bbs-core${NC}"
fi

# Check Python dependencies
echo ""
echo -e "${BLUE}Checking Python environment...${NC}"
echo ""

if [ -d "$PROJECT_ROOT/backend/venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
    
    # Try to activate and check key packages
    if [ -f "$PROJECT_ROOT/backend/venv/bin/python" ]; then
        PYTHON_PATH="$PROJECT_ROOT/backend/venv/bin/python"
        
        # Check for Flask
        if $PYTHON_PATH -c "import flask" 2>/dev/null; then
            FLASK_VERSION=$($PYTHON_PATH -c "import flask; print(flask.__version__)")
            echo -e "${GREEN}✓ Flask installed (version $FLASK_VERSION)${NC}"
        else
            echo -e "${YELLOW}⚠️  Flask not installed in venv${NC}"
        fi
        
        # Check for other key packages
        for pkg in "sqlalchemy" "cryptography" "qrcode"; do
            if $PYTHON_PATH -c "import $pkg" 2>/dev/null; then
                echo -e "${GREEN}✓ $pkg installed${NC}"
            else
                echo -e "${YELLOW}⚠️  $pkg not installed${NC}"
            fi
        done
    fi
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${YELLOW}   Create with: python3 -m venv backend/venv${NC}"
    echo -e "${YELLOW}   Install dependencies with: pip install -r backend/requirements.txt${NC}"
fi

# Check database
echo ""
echo -e "${BLUE}Checking database...${NC}"
echo ""

DB_PATH=$(grep "^DATABASE_URL=" "$ENV_FILE" | cut -d'/' -f2- | cut -d':' -f3-)
if [ -n "$DB_PATH" ]; then
    FULL_DB_PATH="$PROJECT_ROOT/$DB_PATH"
    if [ -f "$FULL_DB_PATH" ]; then
        echo -e "${GREEN}✓ Database file exists: $DB_PATH${NC}"
        DB_SIZE=$(du -h "$FULL_DB_PATH" | cut -f1)
        echo -e "${GREEN}  Size: $DB_SIZE${NC}"
    else
        echo -e "${YELLOW}⚠️  Database file not found (will be created on first run)${NC}"
    fi
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $SECURITY_ISSUES -gt 0 ]; then
    echo -e "${RED}⚠️  $SECURITY_ISSUES security issue(s) found - please review${NC}"
fi

echo ""
echo -e "${GREEN}✓ Environment check complete${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review any warnings or missing configurations above"
echo -e "  2. Edit .env file with your actual values"
echo -e "  3. Generate secure keys where needed"
echo -e "  4. Ensure all required Python packages are installed"
echo -e "  5. Build BBS Core if not already built (make build-bbs-core)"
echo -e "  6. Start the server with: make run"
echo ""

exit 0

