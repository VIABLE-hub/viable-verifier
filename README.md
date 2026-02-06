# VERITAS - Enterprise-Ready Privacy-Preserving Digital Credentials Platform

**Multi-tenant platform for issuing privacy-preserving digital credentials using BBS+ selective-disclosure cryptography**

**Supervisor:** Patrick Herbke (p.herbke@tu-berlin.de)

---

## Project Overview

VERITAS is a multi-tenant platform currently in prototype stage, being developed into a university-ready infrastructure.

---

## Quick Start

### Prerequisites

- **Python 3.12** (verified working: 3.10 & 3.12)
- **Rust** (required for compiling BBS+ core library)
- **For Windows Users:** WSL (Windows Subsystem for Linux) is **strongly recommended** - see [Windows Setup Guide](#-windows-setup-guide) below

#### General (Linux/macOS/WSL)
```bash
# On Ubuntu: essential build tools, git, curl
sudo apt update
sudo apt install build-essential git curl

# Optional: gh to authenticate with GitHub
sudo apt install gh
```

#### Python & venv
```bash
# On Ubuntu:
sudo apt install python3 python3-pip python3-venv
```

#### Rust & Cargo
**Important:** Install via script, not apt, to ensure you have the latest version.
```bash
#
# ⚠️ ATTENTION ⚠️
# This fetches and runs an external script!
# It's the recommended installation method according to:
# https://rust-lang.org/learn/get-started
#
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

#
# IMPORTANT: Restart your terminal for rustc and cargo commands to work!
# Do this BEFORE running 'make setup'!
#
```

### Setup
```bash
# Pull bbs-core submodule
git submodule sync --recursive
git submodule update --init --recursive

# Compile BBS+ core, create venv, and install dependencies
make setup
```

### Start/Stop Tenants

**Start all tenants:**
```bash
make start-all          # Starts all tenants on different ports
```

**Stop all tenants:**
```bash
make stop-all           # Stops all running tenant servers
```

**Start single tenant:**
```bash
make dev-root           # Root tenant (port 8083)
make dev-tub            # TU Berlin (port 8081)
make dev-fub            # FU Berlin (port 8082)
make dev-veritas        # Veritas (port 8080)
```

**Stop single tenant:**
```bash
make kill-port PORT=8081   # Kills process on specified port
```

---

## 🪟 Windows Setup Guide

### **Why WSL is Strongly Recommended for Windows**

The BBS+ core library compiles to native Linux binaries (`.so` files). While the Makefile includes Windows support, **native Windows execution is not fully tested and may not work without pre-compiled Windows binaries (.dll files)**.

**We strongly recommend using WSL (Windows Subsystem for Linux)** for the best experience.

### **Complete Setup for Windows Users (WSL - Recommended)**

#### **Step 1: Install WSL**
```powershell
# Run in PowerShell as Administrator
wsl --install
```
> **Note:** You may need to restart your computer after installation.

#### **Step 2: Open WSL Terminal**
```powershell
# In PowerShell or Windows Terminal
wsl
```

#### **Step 3: Navigate to Your Project**
```bash
cd /mnt/c/path/to/your/project/stvc
```
> **Note:** Replace with your actual project path. Windows drives are mounted under `/mnt/` in WSL.  
> Example: `C:\Users\YourName\Projects\stvc` becomes `/mnt/c/Users/YourName/Projects/stvc`

#### **Step 4: Install Dependencies (One-time Setup)**
```bash
# Update package lists
sudo apt update

# Install essential tools
sudo apt install build-essential git curl make python3 python3-pip python3-venv

# Install Rust (required for BBS+ compilation)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

> **Important:** After installing Rust, close and reopen your terminal, or run `source $HOME/.cargo/env`

#### **Step 5: Clone and Setup Project**
```bash
# Pull submodules
git submodule sync --recursive
git submodule update --init --recursive

# Run setup (compiles BBS+ core and installs dependencies)
make setup
```

#### **Step 6: Run the Application**
```bash
# Run TU Berlin tenant on port 8081
make dev-tub

# OR run other tenants:
make dev-root     # Root tenant (port 8083)
make dev-fub      # FU Berlin (port 8082)
make dev-veritas  # Veritas (port 8080)
```

---

### **Native Windows Setup (Not Recommended)**

If you choose to run natively on Windows without WSL:

1. **Install Python 3.12** from python.org
2. **Install Make for Windows** (via chocolatey: `choco install make`)
3. **Run setup:**
```powershell
   make setup
```
> **Warning:** This will skip BBS+ compilation. The application will NOT work without BBS+ binaries (.dll files).

4. **You'll need to manually obtain Windows-compiled BBS+ binaries** (`.dll` files) and place them in the `backend/` directory.

---

### **Using IntelliJ IDEA with WSL (Windows)**

1. **Configure WSL Python Interpreter:**
    - Go to `File` → `Settings` → `Project` → `Python Interpreter`
    - Click `Add Interpreter` → `On WSL...`
    - Select your WSL distribution (usually "Ubuntu")
    - Choose the Python interpreter: `/mnt/c/path/to/project/.venv/bin/python`

2. **Create Run Configuration:**
    - Go to `Run` → `Edit Configurations`
    - Click `+` → `Python`
    - **Script path:** `/mnt/c/path/to/project/backend/main.py`
    - **Working directory:** `/mnt/c/path/to/project/backend`
    - **Environment variables:**
        - `TENANT_ID=tub`
        - `SERVER_PORT=8081`
    - **Python interpreter:** Select the WSL interpreter you configured

3. **Run the application** using the play button or `Shift+F10`

---

### **Quick Reference for Windows Daily Use**
```bash
# Open WSL
wsl

# Navigate to project
cd /mnt/c/path/to/your/project/stvc

# Run application
make dev-tub
```

---

### **Troubleshooting Windows/WSL Issues**

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'flask'` | Run `make setup` to install dependencies |
| `make: command not found` | Install make: `sudo apt install make` |
| `rustc: command not found` | Install Rust (see Step 4) and restart terminal |
| Virtual environment creation fails | Install python3-venv: `sudo apt install python3-venv` |
| Permission denied errors | Use `sudo` for apt commands (e.g., `sudo apt update`) |
| BBS+ compilation fails | Ensure Rust is installed and terminal is restarted |
| Unicode/Emoji encoding errors in console | These are display-only warnings and don't affect functionality |
| App crashes with "Could not find module" on Windows | You need WSL or Windows-compiled BBS+ binaries (.dll files) |

---

## Project Structure

### Core Backend Modules
```
backend/src/
├── issuer/              # Credential Issuance
│   ├── BBS+ credential signing
│   ├── OID4VC metadata and QR code generation
│   └── Multi-tenant credential templates
│
├── verifier/            # Credential Verification
│   ├── BBS+ proof verification
│   ├── Selective disclosure handling
│   └── OID4VP presentation requests
│
├── auth/                # Authentication System
│   ├── Traditional username/password
│   └── VC-based authentication
│
├── settings/            # System Configuration
│   ├── Tenant configuration and branding
│   ├── Key management (BBS+, JWT, X.509)
│   ├── Selective disclosure settings
│   └── Network API configuration
│
├── tenants/             # Multi-Tenant Management
│   ├── Tenant detection and routing
│   ├── Isolated database per tenant
│   └── Tenant-specific configuration
│
├── validate/            # Credential Validation
│   ├── Credential status management
│   └── Revocation and lifecycle tracking
│
├── plugin_system/       # Plugin Architecture
│   ├── Plugin interface and loader
│   └── Event system for plugins
│
└── models.py            # Database Models
```

### Storage & Crypto Modules
```
plugins/
├── blockchain_storage/  # Blockchain storage plugin
└── ipfs_storage/        # IPFS storage plugin

backend/
├── bbs-core/            # Rust-based BBS+ core library (submodule)
├── issuer/key_generator.py      # BBS+ key generation
└── issuer/tenant_key_generator.py  # Tenant-specific keys
```

### Mobile Applications
```
mobile/
└── ios/                 # iOS Wallet (existing)
    └── [Android wallet to be developed]
```

---

## Development

### Available Make Commands
```bash
# Setup & Installation
make setup              # Full setup: compile BBS+, create venv, install deps
make install            # Install dependencies only (venv must exist)

# Running Tenants
make dev-root           # Start root tenant (port 8083)
make dev-tub            # Start TU Berlin tenant (port 8081)
make dev-fub            # Start FU Berlin tenant (port 8082)
make dev-veritas        # Start Veritas tenant (port 8080)
make start-all          # Start all tenants simultaneously
make stop-all           # Stop all running tenants

# Testing
make test               # Run tests
make setup-test         # Setup testing environment

# Docker
make docker-build       # Build Docker images
make docker-run         # Start Docker containers
make docker-down        # Stop Docker containers

# Utilities
make info               # Show environment information
make clean              # Clean temporary files
make kill-port PORT=8081  # Kill process on specific port
```