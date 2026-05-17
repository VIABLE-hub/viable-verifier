#!/bin/bash

# Generate Self-Signed SSL Certificates for Local VIABLE Credentials Testing
# This simulates production SSL environment for deployment testing

set -e

echo "🔒 Generating Self-Signed SSL Certificates for Local Testing..."

# Generate private key
echo "🔑 Generating private key..."
openssl genrsa -out viable-credentials-local.key 2048

# Generate certificate signing request
echo "📝 Generating certificate signing request..."
openssl req -new -key viable-credentials-local.key -out viable-credentials-local.csr -subj "/C=DE/ST=Berlin/L=Berlin/O=VIABLE Credentials/OU=Development/CN=localhost/emailAddress=dev@viable-credentials.local"

# Generate self-signed certificate
echo "📜 Generating self-signed certificate..."
openssl x509 -req -days 365 -in viable-credentials-local.csr -signkey viable-credentials-local.key -out viable-credentials-local.crt

# Create certificate bundle (some applications need this)
echo "📦 Creating certificate bundle..."
cat viable-credentials-local.crt > viable-credentials-local-bundle.crt

# Set proper permissions
chmod 600 viable-credentials-local.key
chmod 644 viable-credentials-local.crt viable-credentials-local.csr viable-credentials-local-bundle.crt

# Generate certificates for all tenants
echo "🏛️ Generating tenant-specific certificates..."

# TUB (port 8080)
openssl req -new -key viable-credentials-local.key -out tub-local.csr -subj "/C=DE/ST=Berlin/L=Berlin/O=TU Berlin/OU=VIABLE Credentials/CN=localhost/emailAddress=tub@viable-credentials.local"
openssl x509 -req -days 365 -in tub-local.csr -signkey viable-credentials-local.key -out tub-local.crt

# FUB (port 8081)  
openssl req -new -key viable-credentials-local.key -out fub-local.csr -subj "/C=DE/ST=Berlin/L=Berlin/O=FU Berlin/OU=VIABLE Credentials/CN=localhost/emailAddress=fub@viable-credentials.local"
openssl x509 -req -days 365 -in fub-local.csr -signkey viable-credentials-local.key -out fub-local.crt

# Root (port 8082)
openssl req -new -key viable-credentials-local.key -out root-local.csr -subj "/C=DE/ST=Berlin/L=Berlin/O=VIABLE Credentials Root/OU=VIABLE Credentials/CN=localhost/emailAddress=root@viable-credentials.local"
openssl x509 -req -days 365 -in root-local.csr -signkey viable-credentials-local.key -out root-local.crt

# Clean up CSR files
rm *.csr

echo "✅ SSL Certificates generated successfully!"
echo ""
echo "Generated certificates:"
ls -la *.crt *.key
echo ""
echo "🚀 Ready for local HTTPS testing!"
echo ""
echo "To trust these certificates in your browser:"
echo "1. Open Keychain Access (macOS) or Certificate Manager (Windows/Linux)"
echo "2. Import viable-credentials-local.crt"
echo "3. Mark it as trusted for SSL"
echo ""
echo "Local URLs will be:"
echo "- TUB:  https://localhost:8080"
echo "- FUB:  https://localhost:8081" 
echo "- Root: https://localhost:8082" 