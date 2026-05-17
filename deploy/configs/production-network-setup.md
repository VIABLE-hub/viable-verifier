# Production Network Setup for VIABLE Credentials
**Mobile Wallet Access Without Ngrok**

## Quick Setup for Server Deployment

### Step 1: Deploy to Server
```bash
# Deploy using Docker
./deploy.sh docker

# Or deploy with Kubernetes  
./deploy.sh kubernetes
```

### Step 2: Configure Network Mode

**Option A: Public IP (Easiest)**
1. Find your server's public IP: `curl ifconfig.me`
2. In VIABLE Credentials Settings → Network → Select "Public IP"
3. Enter your public IP: `203.0.113.45` (example)
4. Save settings

**Option B: Domain Name (Recommended)**
1. Get domain: `viable-credentials.yourdomain.com`
2. Point DNS A record to server IP
3. In VIABLE Credentials Settings → Network → Select "Domain"
4. Enter domain: `viable-credentials.yourdomain.com`
5. Save settings

### Step 3: SSL Certificate Setup

**For Public IP:**
```bash
# Self-signed certificate (development/testing)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/viable-credentials.key \
  -out /etc/ssl/certs/viable-credentials.crt
```

**For Domain (Recommended):**
```bash
# Let's Encrypt (free, trusted certificates)
sudo apt install certbot
sudo certbot certonly --standalone -d viable-credentials.yourdomain.com
```

### Step 4: Update Environment Configuration

Create/update `.env` file:
```bash
# For Public IP deployment
ENABLE_AUTH=true
ACCESS_PASSWORD=YourSecurePassword
SERVER_HOST=0.0.0.0
SERVER_PORT=8080
USE_HTTPS=true
PUBLIC_IP=203.0.113.45

# For Domain deployment  
ENABLE_AUTH=true
ACCESS_PASSWORD=YourSecurePassword
SERVER_HOST=0.0.0.0
SERVER_PORT=443
USE_HTTPS=true
DOMAIN_NAME=viable-credentials.yourdomain.com
```

### Step 5: Firewall Configuration

```bash
# Allow HTTPS traffic
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp  # If using non-standard port

# For multi-tenant (if needed)
sudo ufw allow 8081/tcp  # FUB tenant
sudo ufw allow 8082/tcp  # ROOT tenant
```

## Network Modes Comparison

| Mode | URL Example | Mobile Access | SSL Required | Best For |
|------|-------------|---------------|--------------|----------|
| **Local + Ngrok** | `https://abc123.ngrok.io` | ✅ Global | ✅ Automatic | Development |
| **Public IP** | `https://203.0.113.45:8080` | ✅ Global | ⚠️ Self-signed | Testing |
| **Domain** | `https://viable-credentials.edu` | ✅ Global | ✅ Let's Encrypt | Production |
| **Cloud LB** | `https://app.university.edu` | ✅ Global | ✅ Managed | Enterprise |

## Automatic Configuration

VIABLE Credentials will automatically detect your network setup:

1. **Start server** on your deployed machine
2. **Go to Settings → Network** in web interface  
3. **Auto-detect** will show your public IP
4. **Select connection mode** (Public IP or Domain)
5. **Save settings** - QR codes automatically update!

## Testing Mobile Access

1. **Generate QR code** in VIABLE Credentials Issuer
2. **Check QR content** - should show your public IP/domain
3. **Scan with mobile wallet** - should connect directly
4. **No ngrok tunneling** involved!

## Troubleshooting

**Mobile wallet can't connect:**
- Check firewall allows port 8080/443
- Verify public IP is accessible: `telnet YOUR_IP 8080`
- Check SSL certificate is valid
- Ensure VIABLE Credentials is running on 0.0.0.0 (not localhost)

**QR codes still show localhost:**
- Update network settings in VIABLE Credentials interface
- Restart VIABLE Credentials service
- Clear browser cache and regenerate QR

**SSL certificate errors:**
- Use Let's Encrypt for trusted certificates
- Or add self-signed cert to mobile device trust store

## Example: Complete University Deployment

```bash
# 1. Server setup
ssh user@viable-credentials.university.edu
git clone https://github.com/pherbke/stvc.git
cd stvc

# 2. Environment setup  
cp env.example .env
# Edit .env with your domain and credentials

# 3. SSL certificate
sudo certbot certonly --standalone -d viable-credentials.university.edu

# 4. Deploy
./deploy.sh docker

# 5. Configure network in web interface
# Visit: https://viable-credentials.university.edu
# Settings → Network → Domain Mode → Save

# 6. Test with mobile wallet
# Generate QR → Should show university domain
```

**Result:** Mobile wallets connect directly to `https://viable-credentials.university.edu` - no ngrok needed! 