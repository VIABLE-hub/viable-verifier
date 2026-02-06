"""
Network Configuration Module

Handles all network-related settings and configuration.
"""

from flask import request, jsonify, current_app
import json
import os
import logging
import socket
import requests
from urllib.parse import urlparse
from sqlalchemy.orm.attributes import flag_modified

from ... import db
from ...models import SystemSettings


# Initialize logger for network module
logger = logging.getLogger(__name__)

# Emergency fallback data
EMERGENCY_NETWORK_DATA = {
    "network_info": {
        "local_ip": "127.0.0.1",
        "public_ip": "Not available",
        "hostname": "localhost",
        "default_port": "8080"
    },
    "network_config": {},
    "status": "emergency_fallback"
}

def get_local_ip():
    """
    Get the local IP address
    """
    try:
        # Create a socket connection to determine the outgoing IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # The IP doesn't need to be reachable
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error getting local IP: {e}")
        return "127.0.0.1"

def get_public_ip():
    """
    Get the public IP address using an external service
    """
    try:
        response = requests.get('https://api.ipify.org', timeout=10)
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Not available"
    except Exception as e:
        logger.error(f"Error getting public IP: {e}")
        return "Not available"

def get_network_information():
    """
    Get comprehensive network information
    """
    try:
        hostname = socket.gethostname()
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        default_port = current_app.config.get('PORT', 8080)
        
        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "public_ip": public_ip,
            "default_port": default_port
        }
    except Exception as e:
        logger.error(f"Error getting network information: {e}")
        return {
            "hostname": "unknown",
            "local_ip": "127.0.0.1",
            "public_ip": "Not available",
            "default_port": 8080
        }

def validate_network_settings(data):
    """
    Validate network settings data - FLEXIBLE validation for Settings UI
    """
    try:
        # 🚨 FLEXIBLE VALIDATION: Only validate fields that are actually present
        # Settings UI might send minimal data (just NGROK URL) or complete data
        
        # Validate use_https (boolean) if present
        if "use_https" in data:
            val = data.get("use_https")
            if isinstance(val, str):
                data["use_https"] = val.lower() == 'true'
            elif not isinstance(val, bool):
                logger.warning(f"Validation failed: use_https is not boolean: {type(val)} {val}")
                return {"valid": False, "message": "use_https must be a boolean"}

        # Validate auto_discovery (boolean) if present
        if "auto_discovery" in data:
            val = data.get("auto_discovery")
            if isinstance(val, str):
                data["auto_discovery"] = val.lower() == 'true'
            elif not isinstance(val, bool):
                logger.warning(f"Validation failed: auto_discovery is not boolean: {type(val)}")
                return {"valid": False, "message": "auto_discovery must be a boolean"}

        # Validate timeout (integer) if present
        if "timeout" in data:
            timeout = data.get("timeout")
            if isinstance(timeout, str):
                try:
                    timeout = int(timeout)
                    data["timeout"] = timeout
                except ValueError:
                    pass # Let next check fail
            
            if not isinstance(timeout, int) or timeout < 1 or timeout > 120:
                logger.warning(f"Validation failed: timeout invalid: {timeout}")
                return {"valid": False, "message": "timeout must be an integer between 1 and 120"}

        # Validate use_ngrok (boolean) if present
        if "use_ngrok" in data:
            val = data.get("use_ngrok")
            if isinstance(val, str):
                data["use_ngrok"] = val.lower() == 'true'
            elif not isinstance(val, bool):
                logger.warning(f"Validation failed: use_ngrok is not boolean: {type(val)}")
                return {"valid": False, "message": "use_ngrok must be a boolean"}

        # Validate ngrok_domain if use_ngrok is True
        if data.get("use_ngrok") and "ngrok_domain" in data:
            ngrok_domain = data.get("ngrok_domain", "")

            # 🚨 FIX: Cleanup input to handle copy-paste errors (trailing slashes)
            if isinstance(ngrok_domain, str):
                ngrok_domain = ngrok_domain.strip().rstrip('/')
                data["ngrok_domain"] = ngrok_domain

            if not ngrok_domain:
                logger.warning("Validation failed: ngrok_domain empty")
                return {"valid": False, "message": "ngrok_domain is required when use_ngrok is true"}

            # Check that ngrok_domain is a valid hostname or URL
            try:
                parsed_url = urlparse(ngrok_domain)
                # 🚨 FIX: Added .ngrok-free.dev to allowed domains list
                if parsed_url.scheme not in ['http', 'https'] and not ngrok_domain.endswith(('.ngrok.io', '.ngrok.app', '.ngrok-free.app', '.ngrok-free.dev')):
                     logger.warning(f"Validation failed: Invalid ngrok_domain: {ngrok_domain}")
                     return {"valid": False, "message": "Invalid ngrok_domain format, must be a valid URL or ngrok domain"}
            except Exception:
                return {"valid": False, "message": "Invalid ngrok_domain format"}

        # Handle legacy format with issuer_ip and verifier_ip
        if "issuer_ip" in data or "verifier_ip" in data:
            legacy_keys = ["issuer_ip", "verifier_ip", "issuer_port", "verifier_port"]
            legacy_format = {}
            
            for key in legacy_keys:
                if key in data:
                    legacy_format[key] = data[key]

            # Merge legacy format into new format
            if legacy_format:
                # Keep legacy keys in data for backward compatibility
                pass

        # Validate default_port if present (accept both string and int)
        if "default_port" in data:
            port = data.get("default_port")
            # Convert string to int if needed
            if isinstance(port, str):
                try:
                    port = int(port)
                except ValueError:
                    logger.warning(f"Validation failed: default_port not int parsable: {port}")
                    return {"valid": False, "message": "default_port must be a valid integer"}
            
            if not isinstance(port, int) or port < 1 or port > 65535:
                logger.warning(f"Validation failed: default_port range: {port}")
                return {"valid": False, "message": "default_port must be an integer between 1 and 65535"}

        # All validations passed
        return {"valid": True}
    except Exception as e:
        logger.error(f"Error validating network settings: {e}")
        return {"valid": False, "message": f"Error validating network settings: {str(e)}"}

def api_network_settings():
    """
    Handle network settings API endpoint
    """
    try:
        system_id = "system"
            
        system_settings = SystemSettings.get_or_create_default()
        
        if request.method == "GET":
            # Return current network settings
            network_settings = system_settings.network_settings or {}
            return jsonify({
                "status": "success",
                "data": network_settings
            }), 200
            
        elif request.method == "POST":
            # Update network settings
            if not request.is_json:
                return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                
            data = request.get_json()
            validation_result = validate_network_settings(data)
            
            if not validation_result["valid"]:
                return jsonify({"status": "error", "message": validation_result["message"]}), 400
            
            # Create backup before saving (temporarily disabled for NGROK fix)
            # create_settings_backup(system_id, backup_type='auto', notes='Auto backup before updating network settings')
            
            # 🚨 SMART MERGE: Merge new data with existing settings instead of replacing
            existing_settings = system_settings.network_settings or {}
            
            # Convert string ports to integers for consistency
            if "default_port" in data and isinstance(data["default_port"], str):
                try:
                    data["default_port"] = int(data["default_port"])
                except ValueError:
                    pass  # Let validation catch this
            
            # 🚨 FIX: Generate ngrok_url if missing so it can be picked up by get_current_server_url
            if data.get("use_ngrok") and data.get("ngrok_domain"):
                domain = data.get("ngrok_domain", "").strip()
                if domain:
                    # Determine scheme
                    scheme = "https"
                    if "use_https" in data:
                        if isinstance(data["use_https"], str):
                            is_https = data["use_https"].lower() == 'true'
                        else:
                            is_https = bool(data["use_https"])
                        scheme = "https" if is_https else "http"
                    
                    # Construct URL
                    if not domain.startswith("http"):
                        data["ngrok_url"] = f"{scheme}://{domain}"
                    elif data.get("ngrok_url") is None: # Only set if header doesn't have it (though UI sends domain)
                         # If domain has scheme, use it as url
                        data["ngrok_url"] = domain
                        # clean domain for storage if checks pass? No, maintain separation usually better but let's stick to generating url.
            
            merged_settings = {**existing_settings, **data}  # New data overrides existing
            
            # Update settings using flag_modified for JSON columns
            system_settings.network_settings = merged_settings
            flag_modified(system_settings, 'network_settings')
            db.session.commit()
            
            logger.info(f"✅ Updated network settings for system {system_id}: {data}")
            logger.info(f"📊 Merged settings: {merged_settings}")
            return jsonify({"status": "success", "message": "Network settings updated", "data": merged_settings}), 200
    except Exception as e:
        logger.error(f"Error handling network settings: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def api_network_info():
    """
    Get network information
    """
    try:
        network_info = get_network_information()
        
        system_id = "system"
            
        system_settings = SystemSettings.get_or_create_default()
        network_config = system_settings.network_settings or {}
        
        return jsonify({
            "network_info": network_info,
            "network_config": network_config,
            "status": "ok"
        }), 200
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        return jsonify(EMERGENCY_NETWORK_DATA), 200

def update_network_config():
    """
    Update network configuration
    """
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        
        system_id = "system"
            
        system_settings = SystemSettings.get_or_create_default()
        
        validation_result = validate_network_settings(data)
        if not validation_result["valid"]:
            return jsonify({"status": "error", "message": validation_result["message"]}), 400
        
        # Create backup before saving (temporarily disabled for NGROK fix)
        # create_settings_backup(system_id, backup_type='auto', notes='Auto backup before updating network configuration')
        
        # 🚨 SMART MERGE: Merge new data with existing settings instead of replacing
        existing_settings = system_settings.network_settings or {}
        
        # Convert string ports to integers for consistency
        if "default_port" in data and isinstance(data["default_port"], str):
            try:
                data["default_port"] = int(data["default_port"])
            except ValueError:
                pass  # Let validation catch this

        # 🚨 FIX: Generate ngrok_url if missing so it can be picked up by get_current_server_url
        if data.get("use_ngrok") and data.get("ngrok_domain"):
            domain = data.get("ngrok_domain", "").strip()
            if domain:
                # Determine scheme
                scheme = "https"
                if "use_https" in data:
                    if isinstance(data["use_https"], str):
                        is_https = data["use_https"].lower() == 'true'
                    else:
                        is_https = bool(data["use_https"])
                    scheme = "https" if is_https else "http"
                
                # Construct URL
                if not domain.startswith("http"):
                    data["ngrok_url"] = f"{scheme}://{domain}"
                elif data.get("ngrok_url") is None: 
                    data["ngrok_url"] = domain
        
        merged_settings = {**existing_settings, **data}  # New data overrides existing
        
        # Update settings using flag_modified for JSON columns
        system_settings.network_settings = merged_settings
        flag_modified(system_settings, 'network_settings')
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": "Network configuration updated successfully",
            "config": merged_settings,
            "data": merged_settings
        }), 200
    except Exception as e:
        logger.error(f"Error updating network configuration: {e}")
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

def settings_network_config():
    """
    Update network configuration from settings page
    """
    return update_network_config()

def settings_network_get():
    """
    Get network settings page
    """
    try:
        return render_template("settings/network.html")
    except Exception as e:
        logger.error(f"Error rendering network settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def update_flask_server_url(ngrok_domain, default_ip, default_port, use_https=True):
    """
    Update Flask server URL based on NGROK domain.

    Note: To play nicely with reverse proxies, SERVER_NAME is only set when
    FORCE_SERVER_NAME=true. Otherwise we rely on the incoming Host/X-Forwarded-* headers.
    """
    force_server_name = os.environ.get('FORCE_SERVER_NAME', 'false').lower() == 'true'
    try:
        # Parse NGROK domain
        parsed_url = urlparse(ngrok_domain)
        
        # Extract hostname from URL if it's a full URL
        if parsed_url.netloc:
            hostname = parsed_url.netloc
        else:
            hostname = ngrok_domain
        
        # Create server URL
        protocol = "https" if use_https else "http"
        server_url = f"{protocol}://{hostname}"
        
        # Update Flask configuration
        if force_server_name:
            current_app.config['SERVER_NAME'] = hostname
        current_app.config['SERVER_URL'] = server_url
        
        logger.info(f"Updated Flask server URL to {server_url} (force_server_name={force_server_name})")
        return server_url
    except Exception as e:
        logger.error(f"Error updating Flask server URL: {e}")
        
        # Fallback to default IP and port
        protocol = "https" if use_https else "http"
        fallback_url = f"{protocol}://{default_ip}:{default_port}"
        
        if force_server_name:
            current_app.config['SERVER_NAME'] = f"{default_ip}:{default_port}"
        current_app.config['SERVER_URL'] = fallback_url
        
        logger.info(f"Fallback to default server URL: {fallback_url} (force_server_name={force_server_name})")
        return fallback_url

# Register routes with blueprint
def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/api/network", methods=["GET", "POST"])
    def bp_api_network_alias():
        """Alias for network settings API endpoint"""
        return api_network_settings()

    @blueprint.route("/settings/api/network", methods=["GET", "POST"])
    def bp_api_network():
        """Main network settings API endpoint that frontend expects"""
        return api_network_settings()
        
    @blueprint.route("/settings/api/network/config", methods=["GET", "POST"])
    def bp_api_network_config():
        return api_network_settings()
        
    @blueprint.route("/settings/api/network-info", methods=["GET"])
    def bp_api_network_info():
        return api_network_info()
    
    @blueprint.route("/api/system/network", methods=["GET"])
    def bp_api_system_network():
        """🔧 FIXED: Main network endpoint for settings page"""
        try:
            # Get current system configuration
            system_id = "system"
            logger.info(f"🌐 Network API - Current system: {system_id}")
                
            # Get system settings
            system_settings = SystemSettings.get_or_create_default()
            network_settings = system_settings.network_settings or {}
            
            # Get network information
            network_info = get_network_information()
            
            # Get Flask server URL
            server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
            
            # Check if it's an NGROK URL
            parsed_url = urlparse(server_url)
            is_ngrok_active = parsed_url.hostname and (
                parsed_url.hostname.endswith('.ngrok.io') or
                parsed_url.hostname.endswith('.ngrok-free.app') or 
                parsed_url.hostname.endswith('.ngrok.app')
            )
            
            # 🚨 ENHANCED: Return comprehensive network data for settings
            response_data = {
                "status": "success",
                "network_info": {
                    "local_ip": network_info.get("local_ip", "127.0.0.1"),
                    "public_ip": network_info.get("public_ip", "Not available"),
                    "hostname": network_info.get("hostname", "localhost"),
                    "default_port": network_info.get("default_port", "8080"),
                    "server_url": server_url,
                    "ngrok_url": server_url if is_ngrok_active else network_settings.get('ngrok_url', ''),
                    "is_ngrok_active": is_ngrok_active
                },
                "network_config": network_settings,
                "system_info": {
                    "system_id": system_id,
                    "system_name": "System" if system_config else "Default"
                }
            }
            
            logger.info(f"🌐 Network API - Returning data for system {system_id}")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ Error in network API: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            
            # 🚨 GRACEFUL FALLBACK: Return minimal working data
            fallback_data = {
                "status": "success",
                "network_info": {
                    "local_ip": "127.0.0.1",
                    "public_ip": "Not available",
                    "hostname": "localhost",
                    "default_port": "8080",
                    "server_url": "https://localhost:8080",
                    "ngrok_url": "",
                    "is_ngrok_active": False
                },
                "network_config": {},
                "system_info": {
                    "system_id": "root",
                    "system_name": "System"
                }
            }
            return jsonify(fallback_data)
    
    @blueprint.route('/api/system/network/config', methods=['POST'])
    def bp_update_network_config():
        return update_network_config()
        
    @blueprint.route("/settings/network/config", methods=["POST"])
    def bp_settings_network_config():
        return settings_network_config()
        
    @blueprint.route("/settings/network", methods=["GET"])
    def bp_settings_network_get():
        return settings_network_get()
        
    @blueprint.route("/api/system/network/debug", methods=["GET"])
    def api_system_network_debug():
        """🚨 FIXED: Debug endpoint for network configuration"""
        try:
            # Get current configuration using system registry
            system_id = "system"
            logger.info(f"🔍 Network debug - Current system: {system_id}")
                
            system_settings = SystemSettings.get_or_create_default()
            network_settings = system_settings.network_settings or {}
            
            # Get Flask configuration
            flask_config = {
                "SERVER_NAME": current_app.config.get('SERVER_NAME'),
                "SERVER_URL": current_app.config.get('SERVER_URL'),
                "APPLICATION_ROOT": current_app.config.get('APPLICATION_ROOT'),
                "PREFERRED_URL_SCHEME": current_app.config.get('PREFERRED_URL_SCHEME')
            }
            
            # Get network information
            network_info = get_network_information()
            
            # 🚨 NEW: Get the actual server URL that should be used
            actual_server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
            
            # Parse the server URL to extract components
            parsed_url = urlparse(actual_server_url)
            is_ngrok_url = parsed_url.hostname and (
                parsed_url.hostname.endswith('.ngrok.io') or
                parsed_url.hostname.endswith('.ngrok-free.app') or 
                parsed_url.hostname.endswith('.ngrok.app')
            )
            
            # 🚨 ENHANCED: Merge actual server URL info with network settings
            enhanced_network_settings = {
                **network_settings,
                # Override with actual server URL info
                'actual_server_url': actual_server_url,
                'use_ngrok': is_ngrok_url,
                'ngrok_domain': actual_server_url if is_ngrok_url else network_settings.get('ngrok_domain', ''),
                'is_ngrok_active': is_ngrok_url
            }
            
            logger.info(f"🔍 Network debug - System ID: {system_id}")
            logger.info(f"🔍 Network debug - SERVER_URL: {actual_server_url}")
            logger.info(f"🔍 Network debug - Is NGROK URL: {is_ngrok_url}")
            
            return jsonify({
                "status": "success",
                "system_id": system_id,
                "system_name": "System" if system_config else "Unknown",
                "network_settings": enhanced_network_settings,
                "flask_config": flask_config,
                "network_info": network_info,
                # 🚨 NEW: Explicit server URL info for frontend
                "server_info": {
                    "current_server_url": actual_server_url,
                    "is_ngrok": is_ngrok_url,
                    "issuer_url": f"{actual_server_url}/issuer",
                    "verifier_url": f"{actual_server_url}/verifier"
                }
            })
        except Exception as e:
            logger.error(f"❌ Error getting network debug info: {e}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return jsonify({"status": "error", "message": str(e)}), 500 