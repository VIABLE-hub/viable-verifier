#!/bin/bash
# Check deployment configuration for StudentVC

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     StudentVC Deployment Configuration Check                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if servers are running
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Checking Running Servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_port() {
    PORT=$1
    TENANT=$2
    if lsof -i:$PORT >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $TENANT${NC} running on port $PORT"
        return 0
    else
        echo -e "${RED}❌ $TENANT${NC} NOT running on port $PORT"
        return 1
    fi
}

RUNNING_COUNT=0

if check_port 8080 "VERITAS"; then ((RUNNING_COUNT++)); fi
if check_port 8081 "TUB    "; then ((RUNNING_COUNT++)); fi
if check_port 8082 "FUB    "; then ((RUNNING_COUNT++)); fi
if check_port 8083 "ROOT   "; then ((RUNNING_COUNT++)); fi

echo ""
if [ $RUNNING_COUNT -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No servers running. Start with: ${BLUE}make dev-all${NC}"
elif [ $RUNNING_COUNT -eq 4 ]; then
    echo -e "${GREEN}🎉 All 4 tenants running!${NC}"
else
    echo -e "${YELLOW}⚠️  Only $RUNNING_COUNT/4 tenants running${NC}"
fi

# Check ngrok status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 Checking Ngrok Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*"' | head -n 1 | cut -d'"' -f4)
    if [ -n "$NGROK_URL" ]; then
        echo -e "${GREEN}✅ Ngrok is running${NC}"
        echo "   Public URL: ${BLUE}$NGROK_URL${NC}"
        echo "   Dashboard: http://localhost:4040"
    else
        echo -e "${YELLOW}⚠️  Ngrok API responding but no tunnels found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ngrok is NOT running${NC}"
    echo "   To start: ${BLUE}ngrok http 8080${NC}"
fi

# Check network configuration for each tenant
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Checking Tenant Network Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

check_tenant_config() {
    TENANT=$1
    PORT=$2
    
    if ! lsof -i:$PORT >/dev/null 2>&1; then
        echo -e "${RED}❌ $TENANT${NC} - Server not running"
        return
    fi
    
    RESPONSE=$(curl -sk "https://localhost:$PORT/api/network/status" 2>/dev/null)
    
    if [ -z "$RESPONSE" ]; then
        echo -e "${YELLOW}⚠️  $TENANT${NC} - Cannot fetch network status"
        return
    fi
    
    SERVER_URL=$(echo "$RESPONSE" | grep -o '"server_url":"[^"]*"' | cut -d'"' -f4)
    USE_NGROK=$(echo "$RESPONSE" | grep -o '"use_ngrok":[^,}]*' | cut -d':' -f2)
    NGROK_CONFIGURED=$(echo "$RESPONSE" | grep -o '"ngrok_url":"[^"]*"' | cut -d'"' -f4)
    
    echo -e "${BLUE}📋 $TENANT Configuration:${NC}"
    
    if [ "$SERVER_URL" != "" ]; then
        echo "   Server URL: $SERVER_URL"
    else
        echo "   Server URL: Not set (using local IP)"
    fi
    
    if [ "$USE_NGROK" = "true" ] && [ "$NGROK_CONFIGURED" != "" ]; then
        echo -e "   ${GREEN}✅ Ngrok configured: $NGROK_CONFIGURED${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Ngrok not configured (using local IP)${NC}"
    fi
    echo ""
}

check_tenant_config "VERITAS" 8080
check_tenant_config "TUB    " 8081
check_tenant_config "FUB    " 8082
check_tenant_config "ROOT   " 8083

# Check local network
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💻 Local Network Information"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Get local IPs
if command -v ifconfig >/dev/null 2>&1; then
    LOCAL_IPS=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
    if [ -n "$LOCAL_IPS" ]; then
        echo "Local IP addresses (for same WiFi access):"
        while IFS= read -r ip; do
            echo "   • https://$ip:8080"
        done <<< "$LOCAL_IPS"
    fi
elif command -v ip >/dev/null 2>&1; then
    LOCAL_IPS=$(ip addr | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1)
    if [ -n "$LOCAL_IPS" ]; then
        echo "Local IP addresses (for same WiFi access):"
        while IFS= read -r ip; do
            echo "   • https://$ip:8080"
        done <<< "$LOCAL_IPS"
    fi
else
    echo "Cannot detect local IP addresses"
fi

# Environment variables
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Environment Variables (Production)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -n "$EXTERNAL_SERVER_URL" ]; then
    echo -e "${GREEN}✅ EXTERNAL_SERVER_URL${NC} = $EXTERNAL_SERVER_URL"
else
    echo -e "${YELLOW}⚠️  EXTERNAL_SERVER_URL${NC} not set (OK for development)"
fi

if [ "$USE_EXTERNAL_URL" = "true" ]; then
    echo -e "${GREEN}✅ USE_EXTERNAL_URL${NC} = true"
else
    echo -e "${YELLOW}⚠️  USE_EXTERNAL_URL${NC} = ${USE_EXTERNAL_URL:-false} (OK for development)"
fi

if [ "$DOCKER_MODE" = "true" ]; then
    echo -e "${BLUE}🐳 DOCKER_MODE${NC} = true"
else
    echo "   DOCKER_MODE = ${DOCKER_MODE:-false}"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Configuration Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $RUNNING_COUNT -eq 4 ]; then
    echo -e "${GREEN}✅ Deployment Status: All servers running${NC}"
elif [ $RUNNING_COUNT -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Deployment Status: Partial ($RUNNING_COUNT/4 servers running)${NC}"
else
    echo -e "${RED}❌ Deployment Status: No servers running${NC}"
    echo "   Start with: ${BLUE}make dev-all${NC}"
fi

echo ""

if curl -s http://localhost:4040/api/tunnels >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ngrok Status: Running${NC}"
    echo "   For mobile testing: Configure ngrok URL in Settings UI"
else
    echo -e "${YELLOW}⚠️  Ngrok Status: Not running${NC}"
    echo "   For same WiFi testing: Use local IP (see above)"
    echo "   For mobile testing: Start ngrok and configure in Settings UI"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Quick Actions:"
echo ""
echo "   Start all servers:  ${BLUE}make dev-all${NC}"
echo "   Stop all servers:   ${BLUE}make stop-all${NC}"
echo "   Start ngrok:        ${BLUE}ngrok http 8080${NC}"
echo "   View logs:          ${BLUE}tail -f logs/veritas.log${NC}"
echo "   Configure ngrok:    ${BLUE}https://localhost:8080/settings${NC}"
echo ""

