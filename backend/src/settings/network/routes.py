from flask import request, jsonify, render_template
import logging
import json
from ... import db
from ...models import SystemSettings
from ..core import create_settings_backup
from . import utils as network_utils
from .. import utils as common_utils

logger = logging.getLogger(__name__)

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    # Register routes from this file only
    @blueprint.route("/settings/network/test", methods=["POST"])
    def settings_network_test():
        """Test network connections"""
        try:
            # Get test parameters
            data = request.json
            target = data.get("target")
            test_type = data.get("type", "http")
            timeout = data.get("timeout", 5)
            
            if not target:
                return jsonify({"status": "error", "message": "Target is required"}), 400
            
            # Perform test based on type
            if test_type == "http":
                # Test HTTP connection
                result = common_utils.test_http_connection(target, timeout)
            elif test_type == "socket":
                # Parse host and port
                if ":" in target:
                    host, port_str = target.split(":", 1)
                    try:
                        port = int(port_str)
                    except ValueError:
                        return jsonify({"status": "error", "message": "Invalid port number"}), 400
                else:
                    host = target
                    port = 80  # Default HTTP port
                
                # Test socket connection
                result = common_utils.test_socket_connection(host, port, timeout)
            else:
                return jsonify({"status": "error", "message": f"Invalid test type: {test_type}"}), 400
            
            # Add target to result
            result["target"] = target
            result["type"] = test_type
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e),
                "target": request.json.get("target", "unknown"),
                "type": request.json.get("type", "unknown")
            }), 500
    
    @blueprint.route("/settings/api/test-ngrok", methods=["POST"])
    def api_test_ngrok():
        """Test NGROK connection"""
        try:
            data = request.json
            ngrok_domain = data.get("ngrok_domain")
            
            if not ngrok_domain:
                return jsonify({"status": "error", "message": "NGROK domain is required"}), 400
            
            # Test connection to NGROK domain
            result = network_utils.test_ngrok_connection(ngrok_domain)
            
            # Add domain to result
            result["domain"] = ngrok_domain
            
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error testing NGROK connection: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e),
                "domain": request.json.get("ngrok_domain", "unknown")
            }), 500
    
    @blueprint.route("/api/system/network/ngrok/auto-detect", methods=["POST"])
    def api_system_network_ngrok_auto_detect():
        """Auto-detect NGROK domain"""
        try:
            # Auto-detect NGROK domain
            domain = network_utils.auto_detect_ngrok_domain()
            
            if not domain:
                return jsonify({
                    "status": "error",
                    "message": "No active NGROK tunnels found"
                }), 404
            
            # Test connection to the domain
            test_result = network_utils.test_ngrok_connection(domain)
            
            return jsonify({
                "status": "success",
                "domain": domain,
                "test_result": test_result
            })
        except Exception as e:
            logger.error(f"Error auto-detecting NGROK domain: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/system/network/refresh", methods=["POST"])
    def api_system_network_refresh():
        """Refresh network information"""
        try:
            # Get network information
            network_info = common_utils.get_network_information()
            
            # Get network configuration
            network_config = network_utils.get_network_config()
            
            # Update local IP in config if auto-discovery is enabled
            if network_config.get("auto_discovery"):
                local_ip = network_info.get("local_ip")
                if local_ip:
                    # Get system settings
                    system_settings = SystemSettings.get_or_create_default()
                    network_settings = system_settings.network_settings or {"network": {}}
                    
                    # Update local IP
                    if "network" not in network_settings:
                        network_settings["network"] = {}
                    
                    network_settings["network"]["local_ip"] = local_ip
                    
                    # Save settings
                    system_settings.network_settings = network_settings
                    db.session.commit()
            
            return jsonify({
                "status": "success",
                "network_info": network_info,
                "network_config": network_config
            })
        except Exception as e:
            logger.error(f"Error refreshing network information: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e)
            }), 500
