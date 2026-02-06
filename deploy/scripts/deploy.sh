#!/bin/bash

# StudentVC Production Deployment Script
# =====================================
# This script automates the deployment of StudentVC application
#
# WHAT THIS SCRIPT DOES:
# ----------------------
# 1. Checks prerequisites (Docker, Docker Compose, kubectl)
# 2. Creates necessary data directories
# 3. Offers two deployment options:
#    - Docker Compose: Single container deployment
#    - Kubernetes: Production-grade deployment with auto-scaling
# 4. Builds Docker images with all dependencies
# 5. Starts containers
# 6. Verifies deployment health
# 7. Displays access URLs and monitoring instructions
#
# DEPLOYMENT MODES:
# -----------------
# Default: Runs the application on port 8080

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null && ! docker-compose --version &> /dev/null; then
        log_error "Docker Compose is not installed."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Create data directories
create_data_directories() {
    log_info "Creating data directories..."
    
    # Create deployment directories if they don't exist
    mkdir -p ../configs/data
    mkdir -p ../configs/static
    mkdir -p ../configs/ssl
    
    log_success "Data directories created"
}

# Check environment configuration
check_environment() {
    log_info "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "deployment.env" ]; then
            log_warning "No .env file found. Copying from deployment.env template..."
            cp deployment.env .env
            log_warning "Please edit .env file with your configuration before proceeding"
            read -p "Press Enter to continue after editing .env file..."
        else
            log_error "No .env or deployment.env file found"
            exit 1
        fi
    fi
    
    log_success "Environment configuration ready"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    cd ../configs
    
    # Single tenant deployment
    log_info "Starting deployment..."
    docker compose up -d --build
    
    log_success "All services started"
    
    cd ..
}

# Deploy with Kubernetes
deploy_kubernetes() {
    log_info "Deploying with Kubernetes..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        echo "Visit: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        log_info "Make sure you have:"
        log_info "  1. A running Kubernetes cluster (Docker Desktop, minikube, etc.)"
        log_info "  2. kubectl configured with proper context"
        log_info "  3. NGINX Ingress Controller installed"
        exit 1
    fi
    
    cd ../configs/kubernetes
    
    log_info "Applying Kubernetes manifests in order..."
    
    # Apply in dependency order
    log_info "1/6 Creating namespace..."
    kubectl apply -f namespace.yaml
    
    log_info "2/6 Creating storage (PVCs)..."
    kubectl apply -f storage.yaml
    
    log_info "3/6 Creating configmaps..."
    kubectl apply -f configmaps.yaml
    
    log_info "4/6 Creating secrets..."
    if [ -f secrets.yaml ]; then
        kubectl apply -f secrets.yaml
    else
        log_warning "secrets.yaml not found - NGROK URLs won't work"
    fi
    
    log_info "5/6 Creating services..."
    kubectl apply -f services.yaml
    
    log_info "6/6 Creating deployments..."
    kubectl apply -f deployments.yaml
    
    # Optional: Apply ingress if available
    if [ -f ingress.yaml ]; then
        log_info "7/7 Creating ingress..."
        kubectl apply -f ingress.yaml
        log_success "Ingress created - configure DNS to point to your cluster"
    else
        log_info "No ingress.yaml found - using NodePort/LoadBalancer"
    fi
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/studentvc-tub deployment/studentvc-fub deployment/studentvc-root -n studentvc
    
    # Show access information
    log_success "Kubernetes deployment completed!"
    log_info "Access via:"
    log_info "  kubectl port-forward -n studentvc svc/studentvc-tub 8080:80"
    log_info "  kubectl port-forward -n studentvc svc/studentvc-fub 8081:80" 
    log_info "  kubectl port-forward -n studentvc svc/studentvc-root 8082:80"
    
    cd ../../scripts
}

# Check deployment health
check_deployment_health() {
    log_info "Checking deployment health..."
    
    sleep 10  # Give services time to start
    
    if [ ! -z "$SINGLE_TENANT" ]; then
        # Single tenant health check
        case $SINGLE_TENANT in
            tub) port=8080 ;;
            fub) port=8081 ;;
            root) port=8082 ;;
        esac
        
        if curl -s -o /dev/null -w "%{http_code}" https://localhost:$port --insecure | grep -q "200"; then
            log_success "$SINGLE_TENANT tenant is healthy"
        else
            log_warning "$SINGLE_TENANT tenant is still starting..."
        fi
    else
        # Multi-tenant health check
        local all_healthy=true
        
        # Check TUB
        if curl -s -o /dev/null -w "%{http_code}" https://localhost:8080 --insecure | grep -q "200"; then
            log_success "TUB tenant (8080) is healthy"
        else
            log_warning "TUB tenant (8080) is still starting..."
            all_healthy=false
        fi
        
        # Check FUB
        if curl -s -o /dev/null -w "%{http_code}" https://localhost:8081 --insecure | grep -q "200"; then
            log_success "FUB tenant (8081) is healthy"
        else
            log_warning "FUB tenant (8081) is still starting..."
            all_healthy=false
        fi
        
        # Check ROOT
        if curl -s -o /dev/null -w "%{http_code}" https://localhost:8082 --insecure | grep -q "200"; then
            log_success "ROOT tenant (8082) is healthy"
        else
            log_warning "ROOT tenant (8082) is still starting..."
            all_healthy=false
        fi
        
        if [ "$all_healthy" = true ]; then
            log_success "All tenants are healthy!"
        else
            log_warning "Some services are still starting. Please wait..."
        fi
    fi
}

# Display access information
display_access_info() {
    echo ""
    echo "======================================"
    echo "        DEPLOYMENT COMPLETE           "
    echo "======================================"
    echo ""
    
    if [ ! -z "$SINGLE_TENANT" ]; then
        echo "SINGLE TENANT MODE: $SINGLE_TENANT"
        case $SINGLE_TENANT in
            tub)
                echo "  TU Berlin: https://localhost:8080"
                ;;
            fub)
                echo "  FU Berlin: https://localhost:8081"
                ;;
            root)
                echo "  Root/Default: https://localhost:8082"
                ;;
        esac
    else
        echo "ACCESS URLS:"
        echo "  TU Berlin (TUB): https://localhost:8080"
        echo "  FU Berlin (FUB): https://localhost:8081"
        echo "  Root/Default: https://localhost:8082"
        echo ""
        echo "  NGINX Proxy: http://localhost"
        echo "  Redis Cache: localhost:6379"
    fi
    
    echo ""
    echo "MONITORING:"
    echo "  View logs: docker compose -f ../configs/docker-compose.yml logs -f"
    echo "  View status: docker ps"
    echo ""
    echo "STOP DEPLOYMENT:"
    echo "  docker compose -f ../configs/docker-compose.yml down"
    echo ""
    echo "======================================"
}

# Main execution
main() {
    echo "======================================"
    echo "   StudentVC Deployment Script        "
    echo "======================================"
    echo ""
    
    # Check if single tenant mode requested
    if [ ! -z "$SINGLE_TENANT" ]; then
        echo "SINGLE TENANT MODE: $SINGLE_TENANT"
        echo ""
    fi
    
    # Run checks
    check_prerequisites
    create_data_directories
    check_environment
    
    # Choose deployment method
    if [ "$1" = "kubernetes" ] || [ "$1" = "k8s" ]; then
        deploy_kubernetes
    else
        deploy_docker_compose
    fi
    
    # Health check
    check_deployment_health
    
    # Display info
    display_access_info
}

# Script usage
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: ./deploy.sh [deployment-type]"
    echo ""
    echo "Deployment Types:"
    echo "  docker-compose (default) - Deploy with Docker Compose"
    echo "  kubernetes, k8s         - Deploy with Kubernetes"
    echo ""
    echo "Single Tenant Mode:"
    echo "  SINGLE_TENANT=tub ./deploy.sh   - Deploy only TUB tenant"
    echo "  SINGLE_TENANT=fub ./deploy.sh   - Deploy only FUB tenant"
    echo "  SINGLE_TENANT=root ./deploy.sh  - Deploy only ROOT tenant"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh                      - Multi-tenant Docker Compose deployment"
    echo "  ./deploy.sh kubernetes           - Multi-tenant Kubernetes deployment"
    echo "  SINGLE_TENANT=tub ./deploy.sh    - Single TUB tenant deployment"
    exit 0
fi

# Run main function
main "$@" 