
import sys
import os
import traceback

# Add backend to path
sys.path.append(os.getcwd())

print("Starting debug...")

try:
    print("Importing create_app from src...")
    from src import create_app
    print("create_app imported.")
    
    print("Creating app...")
    app = create_app()
    print("App created successfully.")
except Exception:
    traceback.print_exc()
