# Makefile for StudentVC Backend Application

BACKEND_DIR = backend
VENV_DIR = .venv
PYTHON = python3
PIP = pip3
PORT = 8080
HOST = 0.0.0.0
BASE_URL = https://localhost:$(PORT)

.PHONY: dev setup install clean kill-port activate info test setup-test dev-all start-all stop-all dev-ngrok docker-build docker-bbs docker-run docker-down test-bbs-linux test-docker-api debug-bbs-docker hot-patch-bbs monitor-bbs predeploy test-bbs-docker setup-bbs use-macos-bbs use-linux-bbs test-startup

# Show environment info
info:
	@echo "BBS Core Backend Information: "
	@echo "Backend-Folder: $(BACKEND_DIR)"
	@echo "Virtual Environment: $(VENV_DIR)"
	@echo "Python: $(PYTHON)"
	@echo "Pip: $(PIP)"
	@echo "Port: $(PORT)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual Environment exists"; \
		echo "Python-Version: $$($(PYTHON) --version 2>&1)"; \
	else \
		echo "Virtual Environment does not exist"; \
	fi

# Start the application (Single Tenant)
dev:
ifeq ($(OS),Windows_NT)
	@echo "Starting StudentVC (Single Tenant) on port 8080"
	cd $(BACKEND_DIR) && set SERVER_PORT=8080&& ..\\$(VENV_DIR)\\Scripts\\python.exe main.py
else
	@echo "Starting StudentVC (Single Tenant) on port 8080"
	cd $(BACKEND_DIR) && SERVER_PORT=8080 ../$(VENV_DIR)/bin/python main.py
endif

# Start default
dev-all: dev
start-all: dev

# Stop server
stop-all:
	@echo "Stopping server on port 8080..."
	@bash -c "lsof -ti:8080 | xargs kill -9 2>/dev/null && echo "  Stopped (port 8080)" || echo "  ⚠️  No server on port 8080""
	@rm -f logs/*.pid 2>/dev/null || true

# Setup virtual environment and dependencies
setup:
ifeq ($(OS),Windows_NT)
	@echo "⚠️  WARNING: Native Windows is not fully supported!"
	@echo "⚠️  BBS+ core library requires Linux binaries."
	@echo "⚠️  Please use WSL (Windows Subsystem for Linux) instead."
	@echo "⚠️  See README.md for Windows setup instructions."
	@echo ""
	@echo "Creating virtual environment: $(VENV_DIR)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies"
	$(VENV_DIR)\\Scripts\\python.exe -m pip install --upgrade pip
	$(VENV_DIR)\\Scripts\\python.exe -m pip install -r $(BACKEND_DIR)/requirements.txt
	@echo ""
	@echo "⚠️  NOTE: BBS+ compilation skipped on Windows."
	@echo "⚠️  The application will NOT work without BBS+ binaries."
	@echo "⚠️  Please switch to WSL for full functionality."
else
	@echo "Compiling bbs-core libs..."
	rm -f $(BACKEND_DIR)/bbs_core.py $(BACKEND_DIR)/libuniffi_bbs_core.*
	cd $(BACKEND_DIR)/bbs-core/python && chmod +x build.sh && ./build.sh
	mv $(BACKEND_DIR)/bbs-core/python/bbs_core.py $(BACKEND_DIR)/
	mv $(BACKEND_DIR)/bbs-core/python/libuniffi_bbs_core.so $(BACKEND_DIR)/ || true
	mv $(BACKEND_DIR)/bbs-core/python/libuniffi_bbs_core.dylib $(BACKEND_DIR)/ || true
	
	@echo "Creating virtual Environment: $(VENV_DIR)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing Dependencies"
	$(VENV_DIR)/bin/pip install --upgrade pip
	$(VENV_DIR)/bin/pip install -r $(BACKEND_DIR)/requirements.txt
endif

# Install dependencies only
install:
	@echo "Installing Dependencies in existing environment"
	$(VENV_DIR)/bin/pip install -r $(BACKEND_DIR)/requirements.txt

# Clean temporary files
clean:
	@echo "Cleaning up temporary files"
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +

# Kill process on port
kill-port:
	@echo "Kill Processes on Port $(PORT)"
	-lsof -ti:$(PORT) | xargs kill -9

# Run tests
test:
	@echo "Starting tests"
	cd $(BACKEND_DIR) && ../$(VENV_DIR)/bin/pytest

# Setup test environment
setup-test:
	@echo "Setting up testing environment"
	$(VENV_DIR)/bin/pip install -r $(BACKEND_DIR)/test/requirements.txt

# Docker commands
docker-build:
	@echo "Building Docker image"
	cd deploy && docker-compose -f configs/docker-compose.yml build

docker-run:
	@echo "Starting Docker container"
	cd deploy && docker-compose -f configs/docker-compose.yml up

docker-down:
	@echo "Stopping Docker container"
	cd deploy && docker-compose -f configs/docker-compose.yml down

# BBS+ Build Management (Legacy/Support)
setup-bbs:
	@chmod +x scripts/testing/setup_bbs_builds.sh
	@./scripts/testing/setup_bbs_builds.sh

