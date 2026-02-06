from flask import request, jsonify, current_app
import requests
from urllib.parse import urlparse
import logging
import json
import socket
import time

from .. import settings
from ...models import SystemSettings
from .config import get_local_ip, update_flask_server_url
from .. import utils as settings_utils

# Initialize logger for ngrok module
logger = logging.getLogger(__name__)

# Try to import ngrok monitor if available
try:
    from ..ngrok_monitor import get_ngrok_monitor, initialize_ngrok_monitoring
    NGROK_MONITOR_AVAILABLE = True
except ImportError:
    logger.warning("NGROK monitor not available")
    NGROK_MONITOR_AVAILABLE = False

def init_ngrok_monitoring():
    """Initialize NGROK monitoring WITHOUT continuous auto-monitoring (disabled for manual-only mode)"""
    global ngrok_monitor
    if NGROK_MONITOR_AVAILABLE:
        try:
            # Initialize monitor object but DO NOT start continuous monitoring
            ngrok_monitor = get_ngrok_monitor()
            # DISABLED: No continuous monitoring to prevent auto-refresh
            # ngrok_monitor.start_monitoring()  # Commented out to disable auto-refresh
            logging.info("NGROK monitor initialized - continuous monitoring DISABLED for manual-only mode")
            return ngrok_monitor
        except Exception as e:
            logger.error(f"Error initializing NGROK monitor: {e}")
    return None

def api_test_ngrok():
    """
    Test NGROK connection
    """
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        ngrok_domain = data.get("ngrok_domain", "")
        
        if not ngrok_domain:
            return jsonify({"status": "error", "message": "Missing ngrok_domain"}), 400
        
        # Check that ngrok_domain is a valid hostname or URL
        try:
            parsed_url = urlparse(ngrok_domain)
            if parsed_url.scheme:
                # If it's a URL, use as is
                ngrok_url = ngrok_domain
            else:
                # If it's just a domain, add https://
                ngrok_url = f"https://{ngrok_domain}"
        except Exception:
            return jsonify({"status": "error", "message": "Invalid ngrok_domain format"}), 400
        
        # Test connection to NGROK domain
        test_result = settings_utils.test_http_connection(ngrok_url)
        
        if test_result["status"] == "success":
            return jsonify({
                "status": "success",
                "message": "NGROK connection successful",
                "test_result": test_result
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": test_result["message"],
                "test_result": test_result
            }), 200  # Return 200 even on error to avoid breaking UI
    except Exception as e:
        logger.error(f"Error testing NGROK connection: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_system_network_ngrok():
    """
    Update NGROK configuration
    """
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        ngrok_domain = data.get("ngrok_domain", "")
        use_https = data.get("use_https", True)
        
        if not ngrok_domain:
            return jsonify({"status": "error", "message": "Missing ngrok_domain"}), 400
        
        # Check that ngrok_domain is a valid hostname or URL
        try:
            parsed_url = urlparse(ngrok_domain)
            if parsed_url.scheme:
                # If it's a URL, extract the hostname
                hostname = parsed_url.netloc
                
                # If the hostname includes a port, remove it
                if ':' in hostname:
                    hostname = hostname.split(':')[0]
            else:
                # If it's just a domain, use as is
                hostname = ngrok_domain
                
            # Check if it's a valid NGROK domain
            if not hostname.endswith(('.ngrok.io', '.ngrok.app', '.ngrok-free.app')):
                return jsonify({"status": "error", "message": "Invalid ngrok_domain, must end with .ngrok.io, .ngrok.app, or .ngrok-free.app"}), 400
        except Exception:
            return jsonify({"status": "error", "message": "Invalid ngrok_domain format"}), 400
        
        # Get system settings
        system_settings = SystemSettings.get_or_create_default()
        
        # Update network settings
        network_settings = system_settings.network_settings or {}
        network_settings["use_ngrok"] = True
        network_settings["ngrok_domain"] = ngrok_domain
        network_settings["use_https"] = use_https
        
        # Save settings
        system_settings.network_settings = network_settings
        from ... import db
        db.session.commit()
        
        # Update Flask server URL
        local_ip = get_local_ip()
        default_port = current_app.config.get('PORT', 8080)
        server_url = update_flask_server_url(ngrok_domain, local_ip, default_port, use_https)
        
        # Test connection to new server URL
        test_url = f"{server_url}/settings/api/network-info"
        test_result = settings_utils.test_http_connection(test_url)
        
        return jsonify({
            "status": "success",
            "message": "NGROK configuration updated",
            "server_url": server_url,
            "test_result": test_result
        }), 200
    except Exception as e:
        logger.error(f"Error updating NGROK configuration: {e}")
        from ... import db
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def api_system_network_ngrok_auto_detect():
    """
    Auto-detect NGROK domain
    """
    try:
        if not NGROK_MONITOR_AVAILABLE:
            return jsonify({"status": "error", "message": "NGROK monitor not available"}), 400
        
        # Initialize NGROK monitor
        ngrok_monitor = initialize_ngrok_monitoring()
        
        if not ngrok_monitor:
            return jsonify({"status": "error", "message": "Failed to initialize NGROK monitor"}), 500
        
        # Try to detect NGROK domain
        ngrok_info = ngrok_monitor.get_ngrok_info()
        
        if ngrok_info and "url" in ngrok_info:
            ngrok_url = ngrok_info["url"]
            
            # Extract hostname
            parsed_url = urlparse(ngrok_url)
            ngrok_domain = parsed_url.netloc
            
            # Test connection to NGROK domain
            test_result = settings_utils.test_http_connection(ngrok_url)
            
            if test_result["status"] == "success":
                return jsonify({
                    "status": "success",
                    "message": "NGROK domain auto-detected",
                    "ngrok_domain": ngrok_domain,
                    "ngrok_url": ngrok_url,
                    "test_result": test_result
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to connect to auto-detected NGROK domain",
                    "ngrok_domain": ngrok_domain,
                    "ngrok_url": ngrok_url,
                    "test_result": test_result
                }), 200  # Return 200 even on error to avoid breaking UI
        else:
            return jsonify({
                "status": "error",
                "message": "No active NGROK tunnel detected"
            }), 200  # Return 200 even on error to avoid breaking UI
    except Exception as e:
        logger.error(f"Error auto-detecting NGROK domain: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_system_network_test_ngrok():
    """
    Test NGROK connection - alias endpoint
    """
    return api_test_ngrok()

def settings_network_ngrok_post():
    """
    Update NGROK configuration - alias endpoint
    """
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        ngrok_domain = data.get("ngrok_domain", "")
        
        # Create request data for system endpoint
        system_data = {
            "ngrok_domain": ngrok_domain,
            "use_https": data.get("use_https", True)
        }
        
        # Forward to system endpoint
        # Here we have to manually call the function because we can't modify the request object
        result = api_system_network_ngrok()
        return result
    except Exception as e:
        logger.error(f"Error updating NGROK configuration: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/test-ngrok", methods=["POST"])
    def bp_api_test_ngrok():
        return api_test_ngrok()
    
    @blueprint.route("/api/system/network/ngrok", methods=["POST"])
    def bp_api_system_network_ngrok():
        return api_system_network_ngrok()
    
    @blueprint.route("/api/system/network/ngrok/auto-detect", methods=["POST"])
    def bp_api_system_network_ngrok_auto_detect():
        return api_system_network_ngrok_auto_detect()
    
    @blueprint.route("/api/system/network/test-ngrok", methods=["POST"])
    def bp_api_system_network_test_ngrok():
        return api_system_network_test_ngrok()
    
    @blueprint.route("/settings/network/ngrok", methods=["POST"])
    def bp_settings_network_ngrok_post():
        return settings_network_ngrok_post() 