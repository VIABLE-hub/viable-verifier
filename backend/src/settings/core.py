from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
import json
import logging
import time
from .. import db
from ..models import SystemSettings, SystemSettingsBackup, VC_validity
from sqlalchemy.orm.attributes import flag_modified
import traceback

# Create the Blueprint
settings = Blueprint('settings', __name__)

# Initialize logger
logger = logging.getLogger(__name__)

# Track application start time for accurate uptime calculation
APP_START_TIME = time.time()

# Emergency fallback system info
EMERGENCY_SYSTEM_INFO = {
    "cpu": {
        "usage": 0,
        "cores": 4,
        "logical_cores": 8,
        "temperature": None
    },
    "memory": {
        "percentage": 0,
        "usage": 0,
        "usage_formatted": "0 B",
        "total": 16000000000,
        "total_formatted": "16.0 GB",
        "available": 16000000000
    },
    "disk": {
        "percentage": 0,
        "usage": 0,
        "usage_formatted": "0 B",
        "total": 500000000000,
        "total_formatted": "500.0 GB",
        "free": 500000000000,
        "free_formatted": "500.0 GB"
    },
    "uptime": {
        "app_uptime": "0:00:00",
        "app_uptime_seconds": 0,
        "system_uptime": "0:00:00",
        "system_uptime_seconds": 0,
        "boot_time": "2025-01-01T00:00:00"
    },
    "database": {
        "credential_count": 0
    },
    "services": {
        "issuer_status": "unknown",
        "verifier_status": "unknown"
    },
    "os": {
        "platform": "Unknown",
        "version": "Unknown",
        "architecture": "Unknown"
    },
    "python": {
        "version": "3.9.0",
        "implementation": "CPython"
    },
    "git": {
        "commit": "unknown"
    },
    "timestamp": "2025-01-01T00:00:00"
}

def initialize_verifier_from_database():
    """
    Initialize verifier presentation definition from database settings
    This function is no longer needed since the verifier now dynamically loads settings
    """
    try:
        # The new verifier system automatically loads settings dynamically
        # No initialization needed since verifier calls get_current_selective_disclosure_settings()
        logger.info("Verifier initialization skipped - using dynamic settings loading")
        return True
    except Exception as e:
        logger.error(f"Error initializing verifier from database: {e}")
        return False

def get_system_settings():
    """Get system settings object"""
    try:
        settings = SystemSettings.get_or_create_default()
        return settings
    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        return None

def get_current_user_email():
    """Get current user's email, with fallback"""
    if current_user and current_user.is_authenticated and hasattr(current_user, 'email'):
        return current_user.email
    return 'system@example.com'

def create_settings_backup(backup_type='manual', notes=None):
    """Create a backup of the current settings"""
    try:
        system_settings = SystemSettings.get_or_create_default()
        if system_settings:
            backup = SystemSettingsBackup(
                backup_data=system_settings.get_all_settings(),
                backup_type=backup_type,
                notes=notes
            )
            db.session.add(backup)
            db.session.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating settings backup: {e}")
    return False

# Register core routes only (submodules register themselves)
def register_routes(blueprint=None):
    """Register core routes only - submodules handle their own registration"""
    if blueprint is None:
        blueprint = settings
    
    @blueprint.route("/settings", methods=["GET"])
    def settings_view():
        """Render the main settings view"""
        try:
            return render_template("settings.html")
        except Exception as e:
            logger.error(f"Error rendering settings: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @blueprint.route("/settings/save", methods=["POST"])
    def save_settings():
        """Save settings (general endpoint)"""
        try:
            data = request.json
            setting_type = data.get('type')
            
            if not setting_type:
                return jsonify({"status": "error", "message": "Setting type is required"}), 400
            
            # Forward to the appropriate endpoint based on type
            if setting_type == "disclosure":
                from .disclosure import api_disclosure_settings
                return api_disclosure_settings()
            elif setting_type == "network":
                from .network.config import api_network_settings
                return api_network_settings()
            elif setting_type == "keys":
                from .keys import api_key_settings
                return api_key_settings()
            elif setting_type == "trust":
                from .trust import api_trust_settings
                return api_trust_settings()
            else:
                return jsonify({"status": "error", "message": f"Unknown setting type: {setting_type}"}), 400
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    @blueprint.route('/vanilla')
    def vanilla_settings():
        """Simple vanilla settings page (useful for debugging)"""
        return render_template('settings/vanilla.html')

    @blueprint.route("/settings/api/stats", methods=["GET"])
    def get_statistics():
        """Get statistics for the dashboard"""
        try:
            # Count active VCs
            vc_count = VC_validity.query.count()
            
            # Count revoked VCs
            revoked_count = VC_validity.query.filter_by(is_valid=False).count()
            
            # Calculate active VCs
            active_count = vc_count - revoked_count
            
            return jsonify({
                "status": "success",
                "data": {
                    "total": vc_count,
                    "active": active_count,
                    "revoked": revoked_count
                }
            })
        except Exception as e:
            logger.error(f"Error fetching statistics: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e),
                "data": {
                    "total": 0,
                    "active": 0,
                    "revoked": 0
                }
            })

    @blueprint.route("/settings/herzchirurg", methods=["GET"])
    def herzchirurg_dashboard():
        """Render the herzchirurg dashboard"""
        return render_template("settings/system_dashboard.html")

    @blueprint.route("/settings/test-modular")
    def settings_test_modular():
        """Test route for modular settings system"""
        return render_template("settings-test-modular.html")
    
    @blueprint.route("/settings/key-management")
    def settings_key_management():
        """Professional key management dashboard"""
        return render_template("settings/key_management.html") 