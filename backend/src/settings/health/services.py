from flask import jsonify, current_app
import requests
import time
import logging
import os
import json
import socket
import ssl
from datetime import datetime

from .. import settings
# from ...models import Settings

# Initialize logger for services health module
logger = logging.getLogger(__name__)

def initialize_verifier_from_database():
    """
    Initialize verifier presentation definition from database settings
    This function is no longer needed since the verifier now dynamically loads settings
    """
    try:
        # The new verifier system automatically loads settings dynamically
        # No initialization needed since verifier calls get_current_selective_disclosure_settings()
        logger.info("🩺 HERZCHIRURG: Verifier initialization skipped - using dynamic settings loading")
        return True
    except Exception as e:
        logger.error(f"🩺 HERZCHIRURG: Error initializing verifier from database: {e}")
        return False

def get_issuer_health():
    """
    Get issuer health status
    """
    try:
        # Get server URL
        server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
        issuer_url = f"{server_url}/issuer"
        
        # Test connection
        start_time = time.time()
        response = requests.get(issuer_url, timeout=5, verify=False)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "endpoint": issuer_url,
            "response_time": round(elapsed_time, 2),
            "status_code": response.status_code,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking issuer health: {e}")
        return {
            "status": "unhealthy",
            "endpoint": issuer_url if 'issuer_url' in locals() else "unknown",
            "response_time": None,
            "status_code": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def issuer_healthcheck():
    """
    Check issuer health
    """
    return jsonify(get_issuer_health())

def get_verifier_health():
    """
    Get verifier health status
    """
    try:
        # Get server URL
        server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
        verifier_url = f"{server_url}/verifier"
        
        # Test connection
        start_time = time.time()
        response = requests.get(verifier_url, timeout=5, verify=False)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "healthy" if response.status_code == 200 else "unhealthy",
            "endpoint": verifier_url,
            "response_time": round(elapsed_time, 2),
            "status_code": response.status_code,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking verifier health: {e}")
        return {
            "status": "unhealthy",
            "endpoint": verifier_url if 'verifier_url' in locals() else "unknown",
            "response_time": None,
            "status_code": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def verifier_healthcheck():
    """
    Check verifier health
    """
    return jsonify(get_verifier_health())

def health_issuer():
    """
    Check issuer health (alias endpoint)
    """
    return issuer_healthcheck()

def health_verifier():
    """
    Check verifier health (alias endpoint)
    """
    return verifier_healthcheck()

def get_websocket_health():
    """
    Get WebSocket health status
    """
    try:
        # In a real implementation, we would check actual WebSocket connections
        # Here we just check if the server is listening on the WebSocket port
        server_host = current_app.config.get('HOST', '0.0.0.0')
        server_port = current_app.config.get('PORT', 8080)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        
        # Check if port is open
        try:
            s.connect((server_host, server_port))
            connected = True
            s.close()
        except:
            connected = False
        
        return {
            "status": "healthy" if connected else "unhealthy",
            "active_connections": 0,  # Would be replaced with real metrics
            "port": str(server_port),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking WebSocket health: {e}")
        return {
            "status": "unhealthy",
            "active_connections": 0,
            "port": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def health_websocket():
    """
    Check WebSocket health
    """
    return jsonify(get_websocket_health())

def get_sse_health():
    """
    Get Server-Sent Events health status
    """
    try:
        # In a real implementation, we would check actual SSE connections
        # Here we just check if the server is running
        return {
            "status": "healthy",
            "active_clients": 0,  # Would be replaced with real metrics
            "events_sent": 0,  # Would be replaced with real metrics
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking SSE health: {e}")
        return {
            "status": "unhealthy",
            "active_clients": 0,
            "events_sent": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def health_sse():
    """
    Check Server-Sent Events health
    """
    return jsonify(get_sse_health())

def get_database_health():
    """
    Get database health status
    """
    try:
        from ... import db
        from ...models import VC_validity
        
        # Test database connection by making a simple query
        start_time = time.time()
        result = VC_validity.query.limit(1).all()
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get database information
        from ..database.info import get_database_info
        db_info = get_database_info()
        
        return {
            "status": "healthy",
            "type": "SQLite",
            "size": db_info.get("size_formatted", "unknown"),
            "response_time": round(elapsed_time, 2),
            "tables": db_info.get("table_count", 0),
            "records": db_info.get("record_count", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error checking database health: {e}")
        return {
            "status": "unhealthy",
            "type": "SQLite",
            "size": "unknown",
            "response_time": None,
            "tables": 0,
            "records": 0,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def health_database():
    """
    Check database health
    """
    return jsonify(get_database_health())

def get_ssl_health():
    """
    Get SSL certificate health status
    """
    try:
        # Get server URL
        server_url = current_app.config.get('SERVER_URL', 'https://localhost:8080')
        
        # Parse URL to get hostname
        from urllib.parse import urlparse
        parsed_url = urlparse(server_url)
        hostname = parsed_url.netloc.split(':')[0]
        
        # Try to get certificate info
        try:
            context = ssl.create_default_context()
            conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=hostname)
            conn.settimeout(5)
            conn.connect((hostname, 443))
            cert = conn.getpeercert()
            conn.close()
            
            # Check expiry date
            from datetime import datetime
            import time
            
            if 'notAfter' in cert:
                expires = cert['notAfter']
                expires_date = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z")
                now = datetime.now()
                days_remaining = (expires_date - now).days
                
                # Determine status based on expiry
                status = "healthy"
                if days_remaining < 7:
                    status = "critical"
                elif days_remaining < 30:
                    status = "warning"
                
                return {
                    "status": status,
                    "certificate_type": "Valid",
                    "expires": expires_date.isoformat(),
                    "days_remaining": days_remaining,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "warning",
                    "certificate_type": "Unknown",
                    "expires": "unknown",
                    "days_remaining": 0,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as cert_error:
            # Self-signed certificate or other SSL issue
            return {
                "status": "warning",
                "certificate_type": "Self-signed or invalid",
                "expires": "unknown",
                "error": str(cert_error),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error checking SSL health: {e}")
        return {
            "status": "warning",
            "certificate_type": "Unknown",
            "expires": "unknown",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def health_ssl():
    """
    Check SSL certificate health
    """
    return jsonify(get_ssl_health())

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/issuer/healthcheck", methods=["GET"])
    def bp_issuer_healthcheck():
        return issuer_healthcheck()
    
    @blueprint.route("/verifier/healthcheck", methods=["GET"])
    def bp_verifier_healthcheck():
        return verifier_healthcheck()
    
    @blueprint.route("/health/issuer", methods=["GET"])
    def bp_health_issuer():
        return health_issuer()
    
    @blueprint.route("/health/verifier", methods=["GET"])
    def bp_health_verifier():
        return health_verifier()
    
    @blueprint.route("/health/websocket", methods=["GET"])
    def bp_health_websocket():
        return health_websocket()
    
    @blueprint.route("/health/sse", methods=["GET"])
    def bp_health_sse():
        return health_sse()
    
    @blueprint.route("/health/database", methods=["GET"])
    def bp_health_database():
        return health_database()
    
    @blueprint.route("/health/ssl", methods=["GET"])
    def bp_health_ssl():
        return health_ssl() 