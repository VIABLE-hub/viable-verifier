#!/bin/bash
# Simple Authentication Setup for VIABLE Credentials
# This script helps you quickly enable password protection

set -e

echo "==========================================="
echo "  VIABLE Credentials Simple Authentication Setup   "
echo "==========================================="
echo

# Function to generate random password
generate_password() {
    openssl rand -base64 12 | tr -d "=+/" | cut -c1-12
}

# Check if .env exists
if [ ! -f "../../.env" ]; then
    echo "Creating .env file from template..."
    cp ../../env.example ../../.env
    echo "✓ Created .env file"
fi

echo "Choose authentication setup:"
echo "1) Password only (simplest)"
echo "2) Password + Email 2FA (more secure)"
echo "3) Custom setup"
echo

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo
        echo "Setting up PASSWORD ONLY authentication..."
        
        # Generate random password or ask for custom
        default_password=$(generate_password)
        echo "Generated password: $default_password"
        read -p "Use this password or enter your own: " custom_password
        
        password=${custom_password:-$default_password}
        
        # Update .env file
        sed -i.bak "s/ENABLE_AUTH=false/ENABLE_AUTH=true/" ../../.env
        sed -i.bak "s/ACCESS_PASSWORD=viable-credentials2024/ACCESS_PASSWORD=$password/" ../../.env
        sed -i.bak "s/REQUIRE_EMAIL_2FA=false/REQUIRE_EMAIL_2FA=false/" ../../.env
        
        echo
        echo "✓ Password authentication enabled!"
        echo "✓ Password: $password"
        echo "✓ Your colleagues will need this password to access VIABLE Credentials"
        ;;
        
    2)
        echo
        echo "Setting up PASSWORD + EMAIL 2FA authentication..."
        
        # Get password
        default_password=$(generate_password)
        echo "Generated password: $default_password"
        read -p "Use this password or enter your own: " custom_password
        password=${custom_password:-$default_password}
        
        # Get email settings
        read -p "Enter your email for receiving verification codes: " admin_email
        read -p "Enter SMTP email (for sending codes): " smtp_email
        read -s -p "Enter SMTP password (will be hidden): " smtp_password
        echo
        
        # Update .env file
        sed -i.bak "s/ENABLE_AUTH=false/ENABLE_AUTH=true/" ../../.env
        sed -i.bak "s/ACCESS_PASSWORD=viable-credentials2024/ACCESS_PASSWORD=$password/" ../../.env
        sed -i.bak "s/REQUIRE_EMAIL_2FA=false/REQUIRE_EMAIL_2FA=true/" ../../.env
        sed -i.bak "s/ADMIN_EMAIL=your-email@example.com/ADMIN_EMAIL=$admin_email/" ../../.env
        sed -i.bak "s/SMTP_EMAIL=your-smtp-email@gmail.com/SMTP_EMAIL=$smtp_email/" ../../.env
        sed -i.bak "s/SMTP_PASSWORD=your-app-password/SMTP_PASSWORD=$smtp_password/" ../../.env
        
        echo
        echo "✓ Password + Email 2FA authentication enabled!"
        echo "✓ Password: $password"
        echo "✓ Email 2FA: $admin_email"
        echo "✓ Your colleagues will need the password AND email verification"
        ;;
        
    3)
        echo
        echo "Custom setup - edit .env file manually"
        echo "Key variables:"
        echo "  ENABLE_AUTH=true"
        echo "  ACCESS_PASSWORD=your_password"
        echo "  REQUIRE_EMAIL_2FA=true/false"
        echo "  ADMIN_EMAIL=your_email"
        ;;
        
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo
echo "==========================================="
echo "           Setup Complete!                 "
echo "==========================================="
echo
echo "Next steps:"
echo "1. Start your server: make dev"
echo "2. Visit: https://localhost:8080"
echo "3. You'll see the login page"
echo "4. Share the password with your colleagues"
echo
echo "To disable authentication later:"
echo "  Set ENABLE_AUTH=false in .env"
echo
echo "To change password later:"
echo "  Edit ACCESS_PASSWORD in .env"
echo 