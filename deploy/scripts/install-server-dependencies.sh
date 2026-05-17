#!/bin/bash

# VIABLE Credentials Server Dependencies Installation Script
# Run this on the production server before deployment

set -e

echo "🚀 Installing VIABLE Credentials Server Dependencies..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    pkg-config \
    libssl-dev \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    nginx \
    docker.io \
    docker-compose \
    ufw

# Install Rust (required for BBS+ core)
echo "🦀 Installing Rust..."
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
    echo "✅ Rust installed successfully"
else
    echo "✅ Rust already installed"
fi

# Install Docker if not already installed
echo "🐳 Setting up Docker..."
systemctl enable docker
systemctl start docker
usermod -aG docker $USER

# Install Let's Encrypt Certbot for SSL
echo "🔒 Installing Let's Encrypt Certbot..."
apt-get install -y certbot python3-certbot-nginx

# Create application directories
echo "📁 Creating application directories..."
mkdir -p /var/log/viable-credentials
mkdir -p /var/backups/viable-credentials
mkdir -p /etc/viable-credentials

# Set up firewall rules
echo "🔥 Setting up firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 8081/tcp
ufw allow 8082/tcp

echo "✅ Server dependencies installation completed!"
echo ""
echo "Next steps:"
echo "1. Run 'source ~/.cargo/env' to load Rust environment"
echo "2. Clone the VIABLE Credentials repository"
echo "3. Run the deployment script"
echo ""
echo "🎯 Server is ready for VIABLE Credentials deployment!" 