#!/bin/bash

# Kubernetes deployment script for StudentVC multi-tenant system

set -e

echo "======================================"
echo "  StudentVC Kubernetes Deployment     "
echo "======================================"
echo ""

# Configuration
NAMESPACE="studentvc"
DOCKER_REGISTRY=""  # Set if using private registry
IMAGE_TAG="latest"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --registry)
            DOCKER_REGISTRY="$2/"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./deploy-kubernetes.sh [options]"
            echo "Options:"
            echo "  --registry <registry>  Docker registry URL"
            echo "  --tag <tag>           Docker image tag (default: latest)"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
echo "Checking prerequisites..."
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl."
    exit 1
fi

if ! kubectl cluster-info &> /dev/null; then
    echo "Error: No Kubernetes cluster connection. Please configure kubectl."
    exit 1
fi

# Create namespace
echo ""
echo "Creating namespace..."
kubectl apply -f ../configs/kubernetes/namespace.yaml

# Wait for namespace
kubectl wait --for=condition=Active namespace/$NAMESPACE

# Create secrets for colleague access
echo ""
echo "Setting up authentication..."
echo "Enter htpasswd entries for colleague access (one per line, empty line to finish):"
echo "Format: colleague@university.edu:password"

AUTH_ENTRIES=""
while true; do
    read -p "> " entry
    if [[ -z "$entry" ]]; then
        break
    fi
    
    # Extract email and password
    email=$(echo "$entry" | cut -d: -f1)
    password=$(echo "$entry" | cut -d: -f2)
    
    # Generate htpasswd entry
    if command -v htpasswd &> /dev/null; then
        hash=$(htpasswd -nbB "$email" "$password")
        AUTH_ENTRIES="${AUTH_ENTRIES}${hash}\n"
    else
        echo "Warning: htpasswd not found. Using placeholder."
        AUTH_ENTRIES="${AUTH_ENTRIES}${email}:\$2y\$10\$PLACEHOLDER\n"
    fi
done

# Create auth secret
if [[ -n "$AUTH_ENTRIES" ]]; then
    echo -e "$AUTH_ENTRIES" | kubectl create secret generic basic-auth \
        --from-file=auth=/dev/stdin \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
fi

# Deploy storage
echo ""
echo "Creating storage volumes..."
kubectl apply -f ../configs/kubernetes/storage.yaml

# Create ConfigMaps
echo ""
echo "Creating ConfigMaps..."
# You would need to create these from your tenant config files
kubectl create configmap tub-config \
    --from-file=backend/src/tenants/instances/tub/config.json \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap fub-config \
    --from-file=backend/src/tenants/instances/fub/config.json \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl create configmap root-config \
    --from-file=backend/src/tenants/instances/root/config.json \
    --namespace=$NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

# Update image in deployments
echo ""
echo "Updating deployment images..."
sed -i.bak "s|image: studentvc:latest|image: ${DOCKER_REGISTRY}studentvc:${IMAGE_TAG}|g" \
    ../configs/kubernetes/deployments.yaml

# Deploy applications
echo ""
echo "Deploying applications..."
kubectl apply -f ../configs/kubernetes/deployments.yaml

# Deploy services
echo ""
echo "Creating services..."
kubectl apply -f ../configs/kubernetes/services.yaml

# Deploy ingress
echo ""
echo "Creating ingress..."
read -p "Enter your domain name (e.g., studentvc.yourdomain.com): " DOMAIN
sed -i.bak "s|studentvc.yourdomain.com|$DOMAIN|g" ../configs/kubernetes/ingress.yaml
kubectl apply -f ../configs/kubernetes/ingress.yaml

# Wait for deployments
echo ""
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment/studentvc-tub -n $NAMESPACE
kubectl rollout status deployment/studentvc-fub -n $NAMESPACE
kubectl rollout status deployment/studentvc-root -n $NAMESPACE

# Show status
echo ""
echo "======================================"
echo "  Deployment Status                   "
echo "======================================"
echo ""

kubectl get all -n $NAMESPACE

echo ""
echo "======================================"
echo "  Access Information                  "
echo "======================================"
echo ""
echo "Domain: https://$DOMAIN"
echo "Tenants:"
echo "  - TU Berlin: https://$DOMAIN/tub"
echo "  - FU Berlin: https://$DOMAIN/fub"
echo "  - Root: https://$DOMAIN/"
echo ""
echo "Colleagues can log in with their email and password."
echo ""

# Cleanup backup files
rm -f ../configs/kubernetes/*.yaml.bak 