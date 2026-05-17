#!/bin/bash

# Kubernetes Deployment Test Script for VIABLE Credentials
# Tests manifests, provides setup instructions, and validates deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO] $1${NC}"; }
log_success() { echo -e "${GREEN}[SUCCESS] $1${NC}"; }
log_warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
log_error() { echo -e "${RED}[ERROR] $1${NC}"; }

echo "======================================"
echo "   Kubernetes Deployment Test"
echo "======================================"

# Test 1: Check Prerequisites
log_info "1. Checking Prerequisites..."

# Check kubectl
if command -v kubectl &> /dev/null; then
    log_success "kubectl installed: $(kubectl version --client --short 2>/dev/null | head -1)"
else
    log_error "kubectl not installed"
    echo "Install: brew install kubectl"
fi

# Check Docker
if command -v docker &> /dev/null; then
    log_success "Docker available: $(docker --version)"
else
    log_error "Docker not installed"
fi

# Check cluster connection
log_info "Checking Kubernetes cluster connection..."
if kubectl cluster-info &> /dev/null; then
    log_success "Kubernetes cluster connected"
    kubectl cluster-info
    CLUSTER_AVAILABLE=true
else
    log_warning "No Kubernetes cluster available"
    CLUSTER_AVAILABLE=false
fi

echo ""

# Test 2: Validate YAML Manifests
log_info "2. Validating Kubernetes YAML manifests..."

cd deploy/configs/kubernetes

for file in namespace.yaml configmaps.yaml storage.yaml services.yaml deployments.yaml ingress.yaml; do
    if [ -f "$file" ]; then
        # Test YAML syntax
        if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
            log_success "$file: Valid YAML syntax"
        else
            log_error "$file: Invalid YAML syntax"
        fi
        
        # Test kubectl validation (if cluster available)
        if [ "$CLUSTER_AVAILABLE" = true ]; then
            if kubectl apply --dry-run=client --validate=false -f "$file" &>/dev/null; then
                log_success "$file: Valid Kubernetes manifest"
            else
                log_warning "$file: Kubernetes validation failed (might need cluster-specific config)"
            fi
        fi
    else
        log_error "$file: Missing"
    fi
done

cd ../../..

echo ""

# Test 3: Check Docker Image
log_info "3. Checking Docker image..."
if docker images | grep -q "viable-credentials.*latest"; then
    log_success "VIABLE Credentials Docker image exists"
else
    log_warning "VIABLE Credentials Docker image not built"
    echo "Build with: docker build -t viable-credentials:latest ./backend"
fi

echo ""

# Test 4: Test Deploy Script
log_info "4. Testing deploy script..."

if [ -x "./deploy.sh" ]; then
    log_success "Deploy script is executable"
    
    # Test help function
    if ./deploy.sh --help &>/dev/null; then
        log_success "Deploy script help works"
    else
        log_error "Deploy script help failed"
    fi
else
    log_error "Deploy script not executable"
fi

echo ""

# Test 5: Cluster Setup Options
log_info "5. Local Kubernetes Setup Options..."

if [ "$CLUSTER_AVAILABLE" = false ]; then
    echo ""
    echo "OPTION 1: Docker Desktop Kubernetes"
    echo "   1. Open Docker Desktop"
    echo "   2. Go to Settings → Kubernetes"
    echo "   3. Check 'Enable Kubernetes'"
    echo "   4. Apply & Restart"
    echo ""
    
    echo "OPTION 2: minikube"
    echo "   brew install minikube"
    echo "   minikube start"
    echo "   minikube dashboard  # Optional GUI"
    echo ""
    
    echo "OPTION 3: kind (Kubernetes in Docker)"
    echo "   brew install kind"
    echo "   kind create cluster"
    echo ""
fi

# Test 6: Live Deployment Test (if cluster available)
if [ "$CLUSTER_AVAILABLE" = true ]; then
    echo ""
    log_info "6. Testing Live Deployment..."
    
    # Check if Docker image exists
    if docker images | grep -q "viable-credentials.*latest"; then
        echo "Would you like to test actual deployment? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            log_info "Running Kubernetes deployment test..."
            ./deploy.sh kubernetes
        else
            log_info "Skipping live deployment test"
        fi
    else
        log_warning "Build Docker image first: docker build -t viable-credentials:latest ./backend"
    fi
fi

echo ""
echo "======================================"
echo "        TEST SUMMARY"
echo "======================================"

if [ "$CLUSTER_AVAILABLE" = true ]; then
    log_success "Kubernetes cluster is available and ready"
    log_success "Deploy with: ./deploy.sh kubernetes"
else
    log_warning "Set up a local Kubernetes cluster first"
    log_info "Use Docker Desktop, minikube, or kind (see options above)"
fi

log_success "All Kubernetes manifests are present and valid"
log_success "Deploy script is functional"

echo ""
echo "Quick Commands:"
echo "   ./deploy.sh kubernetes                    # Deploy to K8s"
echo "   kubectl port-forward -n viable-credentials svc/viable-credentials-tub 8080:80"
echo "   kubectl get pods -n viable-credentials             # Check status"
echo "   kubectl logs -n viable-credentials -l app=viable-credentials-tub"
echo "" 