#!/bin/bash

# 🚀 StudentVC Production Docker Deployment Script
# Handles external server URL configuration for mobile wallet connectivity

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DEPLOY_DIR")"

echo -e "${BLUE}🚀 StudentVC Production Docker Deployment${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to prompt for user input
prompt_input() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [[ -n "$default" ]]; then
        read -p "$prompt [$default]: " result
        result="${result:-$default}"
    else
        read -p "$prompt: " result
    fi
    
    echo "$result"
}

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root is not recommended for Docker deployments"
    read -p "Continue anyway? (y/N): " continue_root
    if [[ ! "$continue_root" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Docker and Docker Compose
echo -e "\n${BLUE}🔍 Checking Prerequisites${NC}"
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are available"

# Navigate to configs directory
cd "$DEPLOY_DIR/configs"

# Check if docker.env already exists
if [[ -f "docker.env" ]]; then
    print_warning "docker.env already exists"
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! "$reconfigure" =~ ^[Yy]$ ]]; then
        print_status "Using existing docker.env configuration"
        USE_EXISTING=true
    fi
fi

# Configuration setup
if [[ "$USE_EXISTING" != "true" ]]; then
    echo -e "\n${BLUE}🌍 Production Server Configuration${NC}"
    echo "=================================================="
    
    echo "Enter your production server details:"
    echo "Examples:"
    echo "  - Domain: studentvc.university.edu"
    echo "  - IP Address: 203.45.67.89"
    echo "  - Local testing: localhost"
    echo ""
    
    PUBLIC_DOMAIN=$(prompt_input "Server domain or IP address" "localhost")
    
    echo -e "\n${BLUE}🔐 SSL Configuration${NC}"
    echo "For production deployment, you need proper SSL certificates."
    echo "Self-signed certificates won't work with mobile wallets."
    echo ""
    
    USE_HTTPS=$(prompt_input "Use HTTPS? (recommended for production)" "y")
    if [[ "$USE_HTTPS" =~ ^[Yy]$ ]]; then
        PROTOCOL="https"
    else
        PROTOCOL="http"
        print_warning "HTTP is not secure and may not work with mobile wallets"
    fi
    
    echo -e "\n${BLUE}🚢 Port Configuration${NC}"
    TUB_PORT=$(prompt_input "TU Berlin tenant port" "8080")
    FUB_PORT=$(prompt_input "FU Berlin tenant port" "8081") 
    ROOT_PORT=$(prompt_input "Root tenant port" "8082")
    
    # Generate docker.env file
    echo -e "\n${BLUE}📝 Generating docker.env configuration${NC}"
    
    cat > docker.env << EOF
# 🚀 StudentVC Production Environment Configuration
# Generated on $(date)

# =============================================================================
# 🌍 PRODUCTION SERVER CONFIGURATION  
# =============================================================================
USE_EXTERNAL_URL=true
PUBLIC_DOMAIN=${PUBLIC_DOMAIN}

# =============================================================================
# 🎓 TU BERLIN (TUB) TENANT - Port ${TUB_PORT}
# =============================================================================
TUB_PUBLIC_DOMAIN=${PUBLIC_DOMAIN}
TUB_PUBLIC_PORT=${TUB_PORT}
TUB_EXTERNAL_SERVER_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${TUB_PORT}
TUB_SOCKET_IO_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${TUB_PORT}
TUB_NGROK_URL=

# =============================================================================
# 🏫 FU BERLIN (FUB) TENANT - Port ${FUB_PORT}
# =============================================================================
FUB_PUBLIC_DOMAIN=${PUBLIC_DOMAIN}
FUB_PUBLIC_PORT=${FUB_PORT}
FUB_EXTERNAL_SERVER_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${FUB_PORT}
FUB_SOCKET_IO_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${FUB_PORT}
FUB_NGROK_URL=

# =============================================================================
# 🏛️ ROOT TENANT - Port ${ROOT_PORT}
# =============================================================================
ROOT_PUBLIC_DOMAIN=${PUBLIC_DOMAIN}
ROOT_PUBLIC_PORT=${ROOT_PORT}
ROOT_EXTERNAL_SERVER_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${ROOT_PORT}
ROOT_SOCKET_IO_URL=${PROTOCOL}://${PUBLIC_DOMAIN}:${ROOT_PORT}
ROOT_NGROK_URL=
EOF
    
    print_status "docker.env configuration created"
fi

# Display configuration summary
echo -e "\n${BLUE}📋 Deployment Summary${NC}"
echo "=================================================="
if [[ -f "docker.env" ]]; then
    echo "Configuration file: docker.env"
    echo ""
    echo "Services will be accessible at:"
    
    # Read configuration
    source docker.env
    
    echo "  🎓 TU Berlin:  ${TUB_EXTERNAL_SERVER_URL}"
    echo "  🏫 FU Berlin:  ${FUB_EXTERNAL_SERVER_URL}" 
    echo "  🏛️ Root:       ${ROOT_EXTERNAL_SERVER_URL}"
    echo ""
    
    if [[ "$PUBLIC_DOMAIN" == "localhost" ]]; then
        print_warning "Using localhost - mobile wallets on other devices won't be able to connect"
        print_warning "For production, use your server's public domain or IP address"
    else
        print_status "External URLs configured - mobile wallets will be able to connect"
    fi
fi

# Docker deployment
echo -e "\n${BLUE}🐳 Docker Deployment${NC}"
echo "=================================================="

read -p "Deploy StudentVC containers now? (Y/n): " deploy_now
if [[ ! "$deploy_now" =~ ^[Nn]$ ]]; then
    
    echo "Stopping any existing containers..."
    docker-compose --env-file docker.env down 2>/dev/null || true
    
    echo "Building and starting containers..."
    if docker-compose --env-file docker.env up -d --build; then
        print_status "Containers deployed successfully"
        
        echo -e "\n${BLUE}🔍 Container Status${NC}"
        docker-compose --env-file docker.env ps
        
        echo -e "\n${BLUE}🌐 Testing Endpoints${NC}"
        sleep 10  # Wait for containers to start
        
        # Test endpoints
        for service in "TUB:${TUB_EXTERNAL_SERVER_URL}" "FUB:${FUB_EXTERNAL_SERVER_URL}" "ROOT:${ROOT_EXTERNAL_SERVER_URL}"; do
            name=$(echo $service | cut -d: -f1)
            url=$(echo $service | cut -d: -f2-)
            
            if curl -k -s "${url}/health" > /dev/null; then
                print_status "$name tenant: $url - OK"
            else
                print_warning "$name tenant: $url - Not responding (may need time to start)"
            fi
        done
        
        echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
        echo "=================================================="
        echo "Your StudentVC system is now running with external URLs."
        echo "QR codes will use the configured external addresses instead of Docker internal IPs."
        echo ""
        echo "Next steps:"
        echo "1. Ensure your firewall allows connections on the configured ports"
        echo "2. Set up proper SSL certificates for production use"
        echo "3. Test mobile wallet connectivity with the QR codes"
        echo ""
        echo "Logs: docker-compose --env-file docker.env logs -f"
        echo "Stop: docker-compose --env-file docker.env down"
        
    else
        print_error "Deployment failed. Check the logs above for details."
        exit 1
    fi
else
    print_status "Configuration saved to docker.env"
    echo "To deploy later, run:"
    echo "  cd $DEPLOY_DIR/configs"
    echo "  docker-compose --env-file docker.env up -d --build"
fi

echo "" 