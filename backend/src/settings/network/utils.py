import logging
import socket
import requests
import time
import re
from urllib.parse import urlparse
import json
from ...models import SystemSettings
from .. import utils as common_utils

logger = logging.getLogger(__name__)

# NGROK monitoring
ngrok_monitor = None

def init_ngrok_monitoring():
    """Initialize NGROK monitoring WITHOUT continuous auto-monitoring (disabled for manual-only mode)"""
    global ngrok_monitor
    if ngrok_monitor is None:
        try:
            # Import NGROK monitoring module
            from .ngrok_monitor import get_ngrok_monitor
            
            # Initialize monitor object but DO NOT start continuous monitoring
            ngrok_monitor = get_ngrok_monitor()
            # DISABLED: No continuous monitoring to prevent auto-refresh
            # ngrok_monitor.start_monitoring()  # Commented out to disable auto-refresh
            logging.info("NGROK monitor initialized - continuous monitoring DISABLED for manual-only mode")
        except Exception as e:
            logging.error(f"Error initializing NGROK monitoring: {e}")
    return ngrok_monitor

def validate_network_settings(data):
    """Validate network settings"""
    try:
        # Validate structure
        if not isinstance(data, dict):
            return False, "Invalid data format"
        
        # Validate network section
        if "network" not in data:
            return False, "Missing network section"
        
        network = data["network"]
        if not isinstance(network, dict):
            return False, "Invalid network format"
        
        # Validate required fields
        required_fields = ["use_https", "default_port", "auto_discovery"]
        for field in required_fields:
            if field not in network:
                return False, f"Missing required field: {field}"
        
        # Validate field types
        if not isinstance(network["use_https"], bool):
            return False, "use_https must be a boolean"
        
        if not isinstance(network["default_port"], int):
            return False, "default_port must be an integer"
        
        if not isinstance(network["auto_discovery"], bool):
            return False, "auto_discovery must be a boolean"
        
        # Validate port range
        if network["default_port"] < 1 or network["default_port"] > 65535:
            return False, "default_port must be between 1 and 65535"
        
        # Validate NGROK settings if present
        if "use_ngrok" in network:
            if not isinstance(network["use_ngrok"], bool):
                return False, "use_ngrok must be a boolean"
            
            if network["use_ngrok"] and "ngrok_domain" in network:
                if not isinstance(network["ngrok_domain"], str):
                    return False, "ngrok_domain must be a string"
                
                # Validate domain format
                domain_pattern = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
                if network["ngrok_domain"] and not domain_pattern.match(network["ngrok_domain"]):
                    return False, "Invalid ngrok_domain format"
        
        # All validations passed
        return True, "Valid"
    except Exception as e:
        logger.error(f"Error validating network settings: {e}")
        return False, str(e)

def update_flask_server_url(ngrok_domain, default_ip, default_port, use_https=True):
    """Update Flask server URL based on network settings"""
    try:
        # Determine the protocol
        protocol = "https" if use_https else "http"
        
        # If NGROK domain is provided, use it
        if ngrok_domain:
            server_url = f"{protocol}://{ngrok_domain}"
            logger.info(f"Using NGROK domain for server URL: {server_url}")
            return server_url
        
        # Otherwise use the local IP and port
        server_url = f"{protocol}://{default_ip}:{default_port}"
        logger.info(f"Using local IP for server URL: {server_url}")
        return server_url
    except Exception as e:
        logger.error(f"Error updating Flask server URL: {e}")
        # Return a default URL as fallback
        return f"{'https' if use_https else 'http'}://localhost:{default_port}"

def get_network_config():
    """Get network configuration"""
    try:
        # Get system settings
        system_settings = SystemSettings.get_or_create_default()
        
        # Get network settings
        network_settings = system_settings.network_settings or {}
        
        # Extract network config
        network_config = network_settings.get("network", {})
        
        # Set defaults if missing
        default_config = {
            "use_https": True,
            "default_port": 8080,
            "auto_discovery": True,
            "use_ngrok": False,
            "ngrok_domain": "",
            "timeout": 30
        }
        
        # Merge with defaults
        for key, value in default_config.items():
            if key not in network_config:
                network_config[key] = value
        
        return network_config
    except Exception as e:
        logger.error(f"Error getting network config: {e}")
        return {
            "use_https": True,
            "default_port": 8080,
            "auto_discovery": True,
            "use_ngrok": False,
            "ngrok_domain": "",
            "timeout": 30
        }

def test_ngrok_connection(ngrok_domain, timeout=5):
    """Test connection to NGROK domain"""
    if not ngrok_domain:
        return {
            "status": "error",
            "message": "NGROK domain not provided",
            "latency": 0
        }
    
    # Add https:// if not present
    if not ngrok_domain.startswith("http"):
        ngrok_url = f"https://{ngrok_domain}"
    else:
        ngrok_url = ngrok_domain
    
    # Test the connection
    return common_utils.test_http_connection(ngrok_url, timeout)

def auto_detect_ngrok_domain():
    """Auto-detect NGROK domain from running tunnels"""
    try:
        # Initialize NGROK monitoring if not already done
        monitor = init_ngrok_monitoring()
        if not monitor:
            return None
        
        # Get active tunnels
        tunnels = monitor.get_active_tunnels()
        if not tunnels:
            return None
        
        # Find a suitable HTTPS tunnel
        for tunnel in tunnels:
            if tunnel.get("proto") == "https" and tunnel.get("public_url"):
                # Extract domain from URL
                url = tunnel["public_url"]
                domain = urlparse(url).netloc
                return domain
        
        return None
    except Exception as e:
        logger.error(f"Error auto-detecting NGROK domain: {e}")
        return None
