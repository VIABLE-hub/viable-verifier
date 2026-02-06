#!/bin/bash

# Script to generate password hashes for colleague access

echo "======================================"
echo "  Password Hash Generator             "
echo "======================================"
echo ""
echo "This generates password hashes for Docker/Traefik authentication"
echo ""

# Function to generate bcrypt hash
generate_hash() {
    local email="$1"
    local password="$2"
    
    # Use htpasswd to generate bcrypt hash
    # The output format is email:hash
    local hash=$(echo "$password" | htpasswd -niB "$email" | cut -d: -f2)
    
    # Docker compose needs escaped $ characters
    local escaped_hash=$(echo "$hash" | sed 's/\$/\$\$/g')
    
    echo "$email:$escaped_hash"
}

# Check if htpasswd is available
if ! command -v htpasswd &> /dev/null; then
    echo "htpasswd not found. Installing apache2-utils..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y apache2-utils
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Please install htpasswd via: brew install httpd"
        exit 1
    fi
fi

# Colleague list
COLLEAGUES=(
    "colleague1@university.edu"
    "colleague2@university.edu"
    "colleague3@university.edu"
)

echo "Generating password hashes for colleagues..."
echo ""

# Store results
RESULTS=()

# Generate passwords for each colleague
for email in "${COLLEAGUES[@]}"; do
    echo "Enter password for $email:"
    read -s password
    echo ""
    
    # Generate hash
    hash_line=$(generate_hash "$email" "$password")
    RESULTS+=("$hash_line")
    
    echo "✓ Hash generated for $email"
    echo ""
done

# Output results
echo "======================================"
echo "  GENERATED HASHES                    "
echo "======================================"
echo ""
echo "Add these to your docker-compose.yml in the basicauth.users section:"
echo ""

# Print all hashes in one line (comma-separated)
result_string=""
for i in "${!RESULTS[@]}"; do
    if [ $i -eq 0 ]; then
        result_string="${RESULTS[$i]}"
    else
        result_string="$result_string,${RESULTS[$i]}"
    fi
done

echo "- \"traefik.http.middlewares.auth.basicauth.users=$result_string\""
echo ""

# Also print individual hashes for reference
echo "Individual hashes:"
echo ""
for result in "${RESULTS[@]}"; do
    echo "$result"
done

echo ""
echo "======================================"
echo "  USAGE INSTRUCTIONS                  "
echo "======================================"
echo ""
echo "1. Copy the generated line above into your docker-compose.yml"
echo "2. Replace 'auth' with your middleware name (e.g., 'tub-auth', 'fub-auth')"
echo "3. Deploy with: docker-compose -f docker-compose-restricted.yml up -d"
echo ""
echo "Colleagues will log in with:"
echo "- Username: their email address"
echo "- Password: the password you just set"
echo "" 