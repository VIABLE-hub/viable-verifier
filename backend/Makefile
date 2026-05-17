# HERZCHIRURG: Simplified Makefile for VIABLE Credentials development

# Default target
.PHONY: all
all: dev

# Start the development server with the venv
.PHONY: dev
dev:
	@echo "🩺 Starting VIABLE Credentials development server using venv..."
	@cd .. && . .venv/bin/activate && cd backend && python main.py


# Create a backup of the database
.PHONY: backup
backup:
	@echo "🗄️ Creating database backup..."
	@cd .. && source venv/bin/activate && cd backend && python -c "from src.settings.settings import create_backup; create_backup()"
	@echo "✅ Backup created successfully in instance/backups/"

# Clean temporary files
.PHONY: clean
clean:
	@echo "🧹 Cleaning temporary files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@rm -rf .pytest_cache
	@rm -rf .coverage
	@echo "✅ Temporary files cleaned"

# Help target
.PHONY: help
help:
	@echo "🩺 VIABLE Credentials Development Commands"
	@echo "--------------------------------"
	@echo "make dev      - Start the development server"
	@echo "make backup   - Create a database backup"
	@echo "make clean    - Remove temporary files"
	@echo "make help     - Show this help message" 