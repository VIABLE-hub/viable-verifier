#!/bin/bash

# Quick setup script for colleague access using Basic Auth
# This creates password-protected access for specific email addresses

echo "======================================"
echo "  Colleague Access Setup              "
echo "======================================"
echo ""

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo ./setup-colleague-access.sh"
    exit 1
fi

# Install required tools
echo "Installing required packages..."
apt-get update -qq
apt-get install -y apache2-utils nginx

# Create password file
echo ""
echo "Creating access for colleagues..."
echo "You'll be prompted to create a password for each email."
echo ""

# List of colleague emails
COLLEAGUES=(
    "colleague1@university.edu"
    "colleague2@university.edu"
    "colleague3@university.edu"
)

# Create htpasswd file
HTPASSWD_FILE="/etc/nginx/.htpasswd_studentvc"

# Add each colleague
for i in "${!COLLEAGUES[@]}"; do
    email="${COLLEAGUES[$i]}"
    
    if [ $i -eq 0 ]; then
        # First user, create new file
        echo "Setting up access for: $email"
        htpasswd -c "$HTPASSWD_FILE" "$email"
    else
        # Additional users, append to file
        echo "Setting up access for: $email"
        htpasswd "$HTPASSWD_FILE" "$email"
    fi
    echo ""
done

# Create NGINX configuration
cat > /etc/nginx/sites-available/studentvc-restricted << 'EOF'
server {
    listen 443 ssl;
    server_name studentvc.yourdomain.com;
    
    # SSL configuration (update paths)
    ssl_certificate /etc/letsencrypt/live/studentvc.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/studentvc.yourdomain.com/privkey.pem;
    
    # Basic authentication for colleagues only
    auth_basic "StudentVC - Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd_studentvc;
    
    # Optional: Allow specific paths without auth
    location /health {
        auth_basic off;
        proxy_pass https://localhost:8082;
    }
    
    # TUB tenant
    location /tub {
        proxy_pass https://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # FUB tenant
    location /fub {
        proxy_pass https://localhost:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # ROOT tenant (default)
    location / {
        proxy_pass https://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name studentvc.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
EOF

echo "======================================"
echo "        SETUP COMPLETE                "
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Update domain name in: /etc/nginx/sites-available/studentvc-restricted"
echo "2. Update SSL certificate paths in the config"
echo "3. Enable the site:"
echo "   ln -s /etc/nginx/sites-available/studentvc-restricted /etc/nginx/sites-enabled/"
echo "4. Test configuration: nginx -t"
echo "5. Reload NGINX: systemctl reload nginx"
echo ""
echo "To add more colleagues later:"
echo "   sudo htpasswd $HTPASSWD_FILE new.colleague@university.edu"
echo ""
echo "To remove access:"
echo "   sudo htpasswd -D $HTPASSWD_FILE colleague@university.edu"
echo ""
echo "Access credentials have been set for:"
for email in "${COLLEAGUES[@]}"; do
    echo "  - $email"
done 