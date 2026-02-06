from flask import request, jsonify, current_app
import socket
import requests
import time
import logging
from urllib.parse import urlparse
import json

from ...models import SystemSettings
from .config import get_local_ip, get_public_ip, get_network_information

# Initialize logger for diagnostics module
logger = logging.getLogger(__name__)

def test_http_connection(url, timeout=5):
    """
    Test HTTP connection to a URL
    """
    try:
        start_time = time.time()
        response = requests.get(url, timeout=timeout, verify=False)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "latency_ms": round(elapsed_time, 2),
            "message": f"HTTP {response.status_code}"
        }
    except requests.exceptions.ConnectTimeout:
        return {"status": "error", "message": "Connection timeout", "status_code": None, "latency_ms": None}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Connection refused", "status_code": None, "latency_ms": None}
    except requests.exceptions.SSLError:
        return {"status": "error", "message": "SSL verification failed", "status_code": None, "latency_ms": None}
    except Exception as e:
        logger.error(f"Error testing HTTP connection to {url}: {e}")
        return {"status": "error", "message": str(e), "status_code": None, "latency_ms": None}

def test_socket_connection(host, port, timeout=5):
    """
    Test socket connection to a host and port
    """
    try:
        # Parse host from URL if it's a URL
        parsed_url = urlparse(host)
        if parsed_url.netloc:
            host = parsed_url.netloc
            
        # Extract port from host if it contains a port
        if ':' in host:
            host, port_str = host.split(':')
            port = int(port_str)
        
        start_time = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "success",
            "message": "Socket connection successful",
            "latency_ms": round(elapsed_time, 2)
        }
    except socket.timeout:
        return {"status": "error", "message": "Connection timeout", "latency_ms": None}
    except socket.error:
        return {"status": "error", "message": "Connection refused", "latency_ms": None}
    except Exception as e:
        logger.error(f"Error testing socket connection to {host}:{port}: {e}")
        return {"status": "error", "message": str(e), "latency_ms": None}

def api_test_connection():
    """
    Test connection to various services
    """
    try:
        if request.method == "GET":
            # Get the URLs to test
            system_settings = SystemSettings.get_or_create_default()
            network_settings = system_settings.network_settings or {}
            
            # Get server URL
            server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
            
            # Get URLs to test
            test_urls = {
                "issuer": f"{server_url}/issuer",
                "verifier": f"{server_url}/verifier",
                "api": f"{server_url}/settings/api/network-info",
                "health": f"{server_url}/health/system"
            }
            
            # Return URLs to test
            return jsonify({"test_urls": test_urls}), 200
            
        elif request.method == "POST":
            # Get URLs to test from request - handle empty/malformed JSON gracefully
            try:
                if request.is_json and request.get_json():
                    data = request.get_json()
                    urls = data.get("urls", {})
                    timeout = data.get("timeout", 5)
                else:
                    # Use default URLs if no JSON data provided
                    logger.info("No JSON data provided, using default connection test URLs")
                    data = {}
                    urls = {}
                    timeout = 5
            except Exception as json_error:
                logger.warning(f"Failed to parse JSON request, using defaults: {json_error}")
                data = {}
                urls = {}
                timeout = 5
            
            # If no URLs provided, use default test URLs
            if not urls:
                server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
                urls = {
                    "issuer": f"{server_url}/issuer",
                    "verifier": f"{server_url}/verifier", 
                    "api": f"{server_url}/api/health",
                    "network": f"{server_url}/api/system/network/debug"
                }
            
            # Test each URL
            results = {}
            for name, url in urls.items():
                results[name] = test_http_connection(url, timeout)
            
            # Count successful tests
            successful_tests = sum(1 for result in results.values() if result["status"] == "success")
            total_tests = len(results)
            
            return jsonify({
                "success": True,
                "results": results,
                "tests_passed": successful_tests,
                "tests_total": total_tests,
                "message": f"Connection test completed: {successful_tests}/{total_tests} services accessible"
            }), 200
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "results": {},
            "tests_passed": 0,
            "tests_total": 0
        }), 200  # Return 200 to avoid triggering frontend HTTP error handling

def api_local_ip():
    """
    Get local IP address
    """
    try:
        local_ip = get_local_ip()
        return jsonify({"local_ip": local_ip}), 200
    except Exception as e:
        logger.error(f"Error getting local IP: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def settings_network_test():
    """
    Test network connectivity - alias endpoint
    """
    return api_test_connection()

def settings_network_test_get():
    """
    Get network test configuration - alias endpoint
    """
    return api_test_connection()

def health_network():
    """
    Get comprehensive network health status
    """
    try:
        # Get network information
        network_info = get_network_information()
        
        # Test connections to key services
        server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
        
        # Test issuer endpoint
        issuer_url = f"{server_url}/issuer"
        issuer_result = test_http_connection(issuer_url)
        
        # Test verifier endpoint
        verifier_url = f"{server_url}/verifier"
        verifier_result = test_http_connection(verifier_url)
        
        # Test API endpoint
        api_url = f"{server_url}/settings/api/network-info"
        api_result = test_http_connection(api_url)
        
        # Test health endpoint
        health_url = f"{server_url}/health/system"
        health_result = test_http_connection(health_url)
        
        # Calculate overall health status
        overall_status = "healthy"
        if any(result["status"] == "error" for result in [issuer_result, verifier_result, api_result, health_result]):
            overall_status = "warning"
        
        return jsonify({
            "status": "success",
            "network_info": network_info,
            "health": {
                "overall_status": overall_status,
                "issuer": issuer_result,
                "verifier": verifier_result,
                "api": api_result,
                "health": health_result
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting network health: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "network_info": {
                "hostname": "unknown",
                "local_ip": "127.0.0.1",
                "public_ip": "unknown",
                "default_port": 8080
            },
            "health": {
                "overall_status": "error",
                "issuer": {"status": "error", "message": "Internal error"},
                "verifier": {"status": "error", "message": "Internal error"},
                "api": {"status": "error", "message": "Internal error"},
                "health": {"status": "error", "message": "Internal error"}
            }
        }), 200  # Return 200 even on error to avoid breaking UI

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/test-connection", methods=["GET", "POST"])
    def bp_api_test_connection():
        return api_test_connection()
    
    @blueprint.route("/settings/api/local_ip", methods=["GET"])
    def bp_api_local_ip():
        return api_local_ip()
    
    @blueprint.route("/settings/network/test", methods=["POST"])
    def bp_settings_network_test():
        return settings_network_test()
    
    @blueprint.route("/settings/network/test", methods=["GET"])
    def bp_settings_network_test_get():
        return settings_network_test_get()
    
    @blueprint.route("/health/network", methods=["GET"])
    def bp_health_network():
        return health_network() 