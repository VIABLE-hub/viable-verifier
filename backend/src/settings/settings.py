"""
Clean, minimal settings.py file.
Most functionality has been moved to modular files.
This file contains only core routes and functions that haven't been moved.
"""

from flask import request, jsonify, render_template, current_app
import logging
import json
import time
import psutil
import os
from .. import db
from ..models import SystemSettings
from .core import settings, create_settings_backup, initialize_verifier_from_database
from . import utils

logger = logging.getLogger(__name__)

# Application start time for uptime calculation
APP_START_TIME = time.time()

# Main settings route is defined in core.py to avoid duplicates

@settings.route("/settings/api/disclosure", methods=["GET", "POST"])
def api_disclosure_settings():
    """API endpoint for selective disclosure settings"""
    system_settings = SystemSettings.get_or_create_default()
    
    if request.method == "GET":
        # Return current settings
        disclosure_settings = system_settings.disclosure_settings or {"selective_disclosure": {"mandatory_fields": []}}
        return jsonify({"status": "success", "data": disclosure_settings})
    
    elif request.method == "POST":
        try:
            data = request.json
            
            # Validate the settings
            from .core import validate_disclosure_settings
            valid, message = validate_disclosure_settings(data)
            if not valid:
                return jsonify({"status": "error", "message": message}), 400
            
            # Create backup
            create_settings_backup("auto", "Before disclosure settings update")
            
            # Update settings
            system_settings.disclosure_settings = data
            db.session.commit()
            
            # Update verifier
            initialize_verifier_from_database()
            
            return jsonify({"status": "success", "message": "Disclosure settings updated"})
        except Exception as e:
            logger.error(f"Error updating disclosure settings: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

@settings.route("/settings/save", methods=["POST"])
def save_settings():
    """Legacy route for saving settings"""
    try:
        data = request.json
        
        # Create backup
        create_settings_backup("manual", "Settings update via legacy route")
        
        # Process the settings update
        # This is a simplified version - specific modules handle their own settings
        
        return jsonify({"status": "success", "message": "Settings saved"})
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@settings.route("/settings/api/stats", methods=["GET"])
def get_statistics():
    """Get system statistics"""
    try:
        # Get basic system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application uptime
        app_uptime = time.time() - APP_START_TIME
        
        # Get credential count from database
        from ..models import VC_validity
        credential_count = VC_validity.query.count()
        
        stats = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "uptime_seconds": app_uptime,
            "credential_count": credential_count,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "disk_total": disk.total,
            "disk_used": disk.used
        }
        
        return jsonify({"status": "success", "data": stats})
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Utility functions that other modules might need
def format_bytes(size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def get_local_ip():
    """Get local IP address"""
    return utils.get_local_ip()

def get_public_ip():
    """Get public IP address"""
    return utils.get_public_ip()

def get_network_information():
    """Get network information"""
    return utils.get_network_information()

# Legacy compatibility functions
def get_current_user_email():
    """Get current user email - legacy function"""
    return "admin@localhost"  # Default for setup