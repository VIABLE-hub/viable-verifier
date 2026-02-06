# 🚀 StudentVC Deployment Guide

**Complete guide for development and production deployment**

---

## 📋 Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Makefile Commands Explained](#makefile-commands-explained)
3. [Ngrok Configuration](#ngrok-configuration)
4. [Production Deployment](#production-deployment)
5. [Troubleshooting](#troubleshooting)

---

## 🛠️ Development Environment Setup

### Prerequisites

```bash
# Required
- Python 3.12+
- Virtual environment (test_env)
- ngrok account (for mobile wallet testing)

# Optional
- Docker (for production testing)
```

### Quick Start

```bash
# 1. Clone repository
cd /path/to/studentvc/

# 2. Setup virtual environment (if not exists)
make setup

# 3. Start development server
make dev
```

---

## 🎯 Makefile Commands Explained

### `make dev` ✅ **RECOMMENDED**

**What it does:**
- Starts the server
- Port: 8080
- Runs with debug mode enabled (if environment supports it)

**Command:**
```bash
make dev
```

**What happens:**
1. Checks for existing server instances
2. Starts Python process: `python main.py`

### `make stop`

**What it does:**
- Stops the running server
- Kills processes on port 8080

**Command:**
```bash
make stop
```

---

## 🌐 Ngrok Configuration

### Understanding URL Priority

The system uses this priority order for server URLs:

```
1. EXTERNAL_SERVER_URL (production)
   ↓ (if not set)
2. System NGROK URL (development/testing)
   ↓ (if not set)
3. Local IP (fallback)
```

### ❌ **Ngrok is NOT default!**

**By default, the system uses:**
- Local IP address (e.g., `https://192.168.178.156:8080`)
- Works for devices on same WiFi network
- **DOES NOT work** for mobile wallets outside your network

### ✅ **How to Enable Ngrok** (For Students)

#### **Method 1: Using Settings UI** (Recommended)

1. **Start ngrok manually:**
   ```bash
   # In separate terminal
   ngrok http https://127.0.0.1:8080 --host-header=rewrite
   ```

2. **Copy the ngrok URL:**
   ```
   https://abc123def456.ngrok-free.app
   ```

3. **Configure in StudentVC:**
   - Open: `https://localhost:8080/settings`
   - Navigate to: **Settings → Network**
   - Enter ngrok domain: `abc123def456.ngrok-free.app`
   - Click "Save Network Settings"

4. **Done!** The system now uses ngrok URL for:
   - QR codes in Issuer
   - QR codes in Verifier
   - All mobile wallet communication

#### **Method 2: Using Makefile** (Advanced)

```bash
# Start ngrok automatically
make dev-ngrok

# Output:
# ✅ ngrok tunnel established:
# 🌐 Public URL: https://abc123.ngrok-free.app
# 🔧 Dashboard: http://localhost:4040
```

Then configure the URL in Settings UI as above.

#### **Method 3: Environment Variable** (CI/CD)

```bash
# Set before starting server
export NGROK_URL=https://your-ngrok-url.ngrok-free.app
make dev
```

### **Ngrok Storage Location**

Ngrok URL is stored in the system database:

```
Database: backend/instance/database.db
Table: system_settings
Column: network_settings
JSON: { "use_ngrok": true, "ngrok_url": "https://..." }
```

### **Verifying Ngrok Configuration**

```bash
# Check what URL is being used
curl -k https://localhost:8080/api/network/status | jq

# Output shows:
# {
#   "server_url": "https://your-ngrok.ngrok-free.app",
#   "use_ngrok": true,
#   "ngrok_url": "https://your-ngrok.ngrok-free.app"
# }
```

---

## 📱 Development Workflow (For Students)

### **Scenario 1: Testing on Same WiFi**

```bash
# 1. Start server
make dev

# 2. Find your local IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# 3. Open on mobile device (same WiFi)
https://192.168.178.156:8080/issuer
```

**No ngrok needed!**

### **Scenario 2: Testing with Remote Device**

```bash
# 1. Start ngrok
ngrok http 8080

# 2. Start server
make dev

# 3. Configure ngrok URL in Settings UI
# Navigate to: https://localhost:8080/settings
# Enter ngrok domain in Network section

# 4. Use from anywhere
https://abc123.ngrok-free.app/issuer
```

---

## 🏭 Production Deployment

### **Option 1: Docker Deployment**

```bash
# 1. Set environment variables
export EXTERNAL_SERVER_URL=https://your-domain.com
export USE_EXTERNAL_URL=true
export DOCKER_MODE=true

# 2. Build and run
docker-compose up -d

# 3. Verify
curl https://your-domain.com/health
```

### **Option 2: Server Deployment (Ubuntu/Nginx)**

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3 python3-pip nginx certbot

# 2. Clone repository
git clone <repo-url> /var/www/studentvc
cd /var/www/studentvc

# 3. Setup virtual environment
python3 -m venv test_env
source test_env/bin/activate
pip install -r backend/requirements.txt

# 4. Configure systemd services
# Create: /etc/systemd/system/studentvc.service
# See: deploy/configs/systemd/studentvc.service

# 5. Start services
sudo systemctl start studentvc

# 6. Configure Nginx reverse proxy
# Copy: deploy/configs/nginx/studentvc.conf
sudo systemctl restart nginx

# 7. Setup SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

### **Environment Variables for Production**

```bash
# Required
EXTERNAL_SERVER_URL=https://your-domain.com
USE_EXTERNAL_URL=true

# Optional
DOCKER_MODE=true              # If using Docker
SERVER_PORT=8080              # Default port
```

---

## 🔍 URL Resolution Logic

### Code Location: `backend/src/utils.py`

```python
def get_current_server_url():
    # Priority 1: EXTERNAL_SERVER_URL (production)
    if os.environ.get('USE_EXTERNAL_URL') == 'true':
        return os.environ.get('EXTERNAL_SERVER_URL')
    
    # Priority 2: System NGROK URL (development)
    system_settings = SystemSettings.get_or_create_default()
    if system_settings.network_settings.get('use_ngrok'):
        return system_settings.network_settings['ngrok_url']
    
    # Priority 3: Local IP (fallback)
    return f"https://{get_local_ip()}:{port}"
```

### **When Each URL is Used:**

| Scenario | URL Used | Set Via |
|----------|----------|---------|
| Local WiFi testing | `https://192.168.x.x:8080` | Automatic |
| Ngrok testing | `https://xxx.ngrok-free.app` | Settings UI |
| Production | `https://your-domain.com` | Environment variable |

---

## 🧪 Testing Checklist

### **Before Students Start:**

- [ ] Virtual environment setup: `make setup`
- [ ] All dependencies installed: `pip list`
- [ ] Ngrok account created (optional)
- [ ] Can access `https://localhost:8080`

### **Development Testing:**

- [ ] Server starts: `make dev`
- [ ] Can access server URL
- [ ] Settings page loads
- [ ] Can configure ngrok URL
- [ ] QR codes generate correctly

### **Mobile Wallet Testing:**

- [ ] Ngrok configured and running
- [ ] Can access issuer from mobile
- [ ] Can scan QR code
- [ ] Credential issuance works
- [ ] Credential verification works

---

## 🐛 Troubleshooting

### **Problem: "Address already in use"**

```bash
# Check what's using the port
lsof -i :8080

# Stop server
make stop

# Restart
make dev
```

### **Problem: "Ngrok URL not working"**

```bash
# 1. Check ngrok is running
curl http://localhost:4040/api/tunnels

# 2. Verify configuration
curl -k https://localhost:8080/api/network/status | jq

# 3. Update in Settings UI
# Go to: Settings → Network → Enter ngrok domain
```

### **Problem: "Selective disclosure not working"**

```bash
# 1. Check database
python3 scripts/check_selective_disclosure_db.py

# 2. Restart server
make stop
make dev

# 3. Check logs
tail -f logs/service.log | grep "SELECTIVE DISCLOSURE"
```

---

## 📊 Server Status Check

### **Check Running Server:**

```bash
# List process
lsof -i :8080 | grep LISTEN

# Check logs
tail -f logs/*.log
```

### **Check Configuration:**

```bash
# Database settings
python3 scripts/check_selective_disclosure_db.py

# Network settings
curl -k https://localhost:8080/api/network/status
```

---

## 📚 Quick Reference

### **Start Development:**

```bash
make dev              # Start server
make stop             # Stop server
```

### **Configure Ngrok:**

```bash
ngrok http 8080           # Start ngrok
# Then: Settings UI → Network → Enter domain
```

### **Check Status:**

```bash
lsof -i :8080             # Check port
tail -f logs/service.log  # Watch logs
python3 scripts/check_selective_disclosure_db.py  # Check DB
```

### **Access URLs:**

```
Local:   https://localhost:8080/

Mobile:  https://your-ngrok.ngrok-free.app/
```

---

## ✅ Summary for Students

### **To Run Development Environment:**

1. **Start server:**
   ```bash
   make dev
   ```

2. **For local testing (same WiFi):**
   - Open `https://localhost:8080` in browser
   - Use local IP on mobile devices

3. **For remote testing (mobile wallet):**
   ```bash
   # Terminal 1: Start ngrok
   ngrok http 8080
   
   # Copy ngrok URL, then:
   # Browser: Settings → Network → Enter ngrok domain → Save
   ```

4. **To stop:**
   ```bash
   make stop
   ```

### **Ngrok is NOT Default:**
- System uses local IP by default
- Configure ngrok URL in Settings UI
- Ngrok is optional (only needed for remote access)

### **For Production:**
- Set `EXTERNAL_SERVER_URL` environment variable
- Use reverse proxy (Nginx)
- No ngrok needed

---

**Last Updated:** 2026-01-19  
**Version:** 3.0  
**Status:** ✅ Production Ready
