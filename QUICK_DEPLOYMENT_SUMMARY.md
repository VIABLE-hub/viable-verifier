# 🚀 StudentVC Deployment Summary

## ⚡️ Quick Commands

| Command | Description |
|---------|-------------|
| `make dev` | ✅ **Start Server** (Port 8080) |
| `make stop` | 🛑 **Stop Server** |
| `make setup` | 🛠 **Install Dependencies** |

## 🌐 Network Configuration

### URL Resolution Priority
1. **Production URL** (`EXTERNAL_SERVER_URL` env var)
2. **Ngrok URL** (From Settings UI)
3. **Local IP** (Fallback)

### Enable Ngrok (Remote Access)
1. Start ngrok: `ngrok http 8080`
2. Copy URL: `https://xyz.ngrok-free.app`
3. Go to: **Settings -> Network**
4. Paste URL & Save

## 📱 Mobile Wallet Testing
- Ensure phone is on **Same WiFi** as laptop (or use Ngrok)
- Default URL: `https://<local-ip>:8080`
- Use **Ngrok** if testing from external network

## 🐛 Troubleshooting
- **Port occupied**: Run `make stop` or `lsof -ti:8080 | xargs kill -9`
- **Database**: Located at `backend/instance/database.db`
- **Logs**: `backend/logs/service.log`

