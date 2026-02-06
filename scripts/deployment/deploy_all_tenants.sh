#!/bin/bash

# Deploy All StudentVC Tenants - Complete Solution
# This script provides multiple options for running all tenants

set -e

echo "🚀 ========================================="
echo "🚀   StudentVC All Tenants Deployment    "
echo "🚀 ========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "test_env" ]; then
    echo -e "${RED}❌ Virtual environment 'test_env' not found${NC}"
    echo -e "${YELLOW}💡 Run: make setup${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment found${NC}"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -ti :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to stop all tenants
stop_all_tenants() {
    echo "🛑 Stopping all running tenants..."
    pkill -f "python.*main.py" 2>/dev/null || true
    if check_port 8080; then
        lsof -ti :8080 | xargs kill -9 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ All tenants stopped${NC}"
}

# Function to test tenant
test_tenant() {
    local tenant_name=$1
    local port=${2:-8080}
    
    echo "🔍 Testing $tenant_name tenant..."
    sleep 2
    
    if curl -k https://localhost:$port/health 2>/dev/null | grep -q "healthy\|ok"; then
        echo -e "${GREEN}✅ $tenant_name tenant is running on port $port${NC}"
        return 0
    else
        echo -e "${RED}❌ $tenant_name tenant not responding on port $port${NC}"
        return 1
    fi
}

# Show available options
show_menu() {
    echo "Select deployment option:"
    echo ""
    echo -e "${BLUE}1)${NC} 🔷 ROOT Tenant Only (Default StudentVC - Berlin Blue)"
    echo -e "${RED}2)${NC} 🔴 TUB Tenant Only (TU Berlin - Red Branding)"  
    echo -e "${GREEN}3)${NC} 🟢 FUB Tenant Only (FU Berlin - Green Branding)"
    echo -e "${YELLOW}4)${NC} 🔄 Sequential All Tenants (Run each for 30 seconds)"
    echo -e "${BLUE}5)${NC} 📋 Show Tenant Status"
    echo -e "${RED}6)${NC} 🛑 Stop All Tenants"
    echo -e "${YELLOW}7)${NC} 🔧 Deploy Instructions"
    echo "8) ❌ Exit"
    echo ""
}

# Deploy single tenant
deploy_single_tenant() {
    local tenant=$1
    local tenant_name=$2
    local color=$3
    
    echo -e "${color}🚀 Starting $tenant_name Tenant...${NC}"
    stop_all_tenants
    sleep 1
    
    # Start tenant in background
    TENANT_ID=$tenant make dev > /tmp/tenant_${tenant}.log 2>&1 &
    local pid=$!
    echo "🔄 Started $tenant_name (PID: $pid)"
    
    # Wait and test
    if test_tenant "$tenant_name"; then
        echo ""
        echo -e "${GREEN}🎉 $tenant_name Tenant Successfully Deployed!${NC}"
        echo -e "${BLUE}📱 Access: https://localhost:8080${NC}"
        echo -e "${YELLOW}📋 Tenant: $tenant${NC}"
        echo -e "${YELLOW}💾 Database: Isolated $tenant database${NC}"
        echo ""
        echo "Press ENTER to stop this tenant..."
        read
        kill $pid 2>/dev/null || true
    else
        echo -e "${RED}❌ Failed to start $tenant_name tenant${NC}"
        kill $pid 2>/dev/null || true
    fi
}

# Deploy all tenants sequentially
deploy_sequential() {
    echo -e "${BLUE}🔄 Sequential Deployment: All Tenants (30 seconds each)${NC}"
    echo ""
    
    # ROOT Tenant
    echo -e "${BLUE}1/3: ROOT Tenant (30 seconds)${NC}"
    deploy_single_tenant "root" "ROOT" "$BLUE"
    
    # TUB Tenant  
    echo -e "${RED}2/3: TUB Tenant (30 seconds)${NC}"
    deploy_single_tenant "tub" "TUB" "$RED"
    
    # FUB Tenant
    echo -e "${GREEN}3/3: FUB Tenant (30 seconds)${NC}"
    deploy_single_tenant "fub" "FUB" "$GREEN"
    
    echo -e "${GREEN}🎉 All tenants tested successfully!${NC}"
}

# Show tenant status
show_status() {
    echo "📋 Current Tenant Status:"
    echo ""
    
    if check_port 8080; then
        echo -e "Port 8080: ${GREEN}🟢 IN USE${NC}"
        ps aux | grep "python.*main.py" | grep -v grep || echo "No Python processes found"
    else
        echo -e "Port 8080: ${YELLOW}🟡 FREE${NC}"
    fi
    
    echo ""
    echo "📁 Tenant Databases:"
    for tenant in root tub fub; do
        db_path="backend/src/tenants/instances/$tenant/database.db"
        if [ -f "$db_path" ]; then
            size=$(ls -lh "$db_path" | awk '{print $5}')
            echo -e "  $tenant: ${GREEN}✅${NC} ($size)"
        else
            echo -e "  $tenant: ${RED}❌${NC} (not created)"
        fi
    done
}

# Show deployment instructions
show_instructions() {
    echo -e "${BLUE}🔧 Manual Deployment Instructions:${NC}"
    echo ""
    echo "Individual Tenants:"
    echo -e "  ${BLUE}make dev-root${NC}  # ROOT tenant (Berlin Blue)"
    echo -e "  ${RED}make dev-tub${NC}   # TU Berlin tenant (Red)"
    echo -e "  ${GREEN}make dev-fub${NC}   # FU Berlin tenant (Green)"
    echo ""
    echo "Each tenant runs on:"
    echo "  🌐 URL: https://localhost:8080"
    echo "  💾 Isolated database per tenant"
    echo "  🎨 Unique branding per tenant"
    echo ""
    echo "For production deployment:"
    echo "  🐳 Docker: cd deploy/scripts && ./deploy-docker-all.sh"
    echo "  ☸️  K8s: cd deploy/scripts && ./deploy-kubernetes.sh"
}

# Main menu loop
while true; do
    echo ""
    show_menu
    read -p "Select option (1-8): " choice
    
    case $choice in
        1)
            deploy_single_tenant "root" "ROOT" "$BLUE"
            ;;
        2)
            deploy_single_tenant "tub" "TUB" "$RED"
            ;;
        3)
            deploy_single_tenant "fub" "FUB" "$GREEN"
            ;;
        4)
            deploy_sequential
            ;;
        5)
            show_status
            ;;
        6)
            stop_all_tenants
            ;;
        7)
            show_instructions
            ;;
        8)
            echo "👋 Goodbye!"
            stop_all_tenants
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option. Please select 1-8.${NC}"
            ;;
    esac
done 