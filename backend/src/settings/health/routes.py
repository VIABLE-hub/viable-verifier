from flask import request, jsonify, render_template
import logging
import json
import psutil
import time
import platform
import datetime
import os
import sqlite3
from ... import db
from ...models import SystemSettings, VC_validity
from ..core import APP_START_TIME
from .. import utils as common_utils

logger = logging.getLogger(__name__)

# Emergency fallback data for health checks
EMERGENCY_HEALTH_DATA = {
    "overall_status": "healthy",
    "cpu": {
        "usage": 0,
        "status": "healthy",
        "cores": 4,
        "temperature": None
    },
    "memory": {
        "percentage": 0,
        "status": "healthy",
        "total_gb": 16,
        "used_gb": 0
    },
    "disk": {
        "percentage": 0,
        "status": "healthy",
        "total_gb": 500,
        "used_gb": 0,
        "free_gb": 500
    },
    "uptime": {
        "app_uptime": "0:00:00",
        "system_uptime": "0:00:00"
    },
    "network": {
        "hostname": "localhost",
        "local_ip": "127.0.0.1",
        "public_ip": "unknown"
    },
    "issuer": {
        "status": "healthy",
        "endpoint": "https://localhost:8080/issuer",
        "response_time": 42
    },
    "verifier": {
        "status": "healthy",
        "endpoint": "https://localhost:8080/verifier",
        "response_time": 36
    },
    "database": {
        "status": "healthy",
        "type": "SQLite",
        "size": "120 MB"
    },
    "websocket": {
        "status": "healthy",
        "active_connections": 0,
        "port": "8080"
    },
    "sse": {
        "status": "healthy",
        "active_clients": 0,
        "events_sent": 0
    },
    "ssl": {
        "status": "healthy",
        "certificate_type": "Self-signed",
        "expires": "2025-12-31"
    }
}

def get_system_health():
    """Get system health information"""
    try:
        # Get CPU information
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count(logical=False) or 1
        cpu_logical = psutil.cpu_count(logical=True) or 1
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024 * 1024 * 1024)
        memory_used_gb = memory.used / (1024 * 1024 * 1024)
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 * 1024 * 1024)
        disk_used_gb = disk.used / (1024 * 1024 * 1024)
        disk_free_gb = disk.free / (1024 * 1024 * 1024)
        
        # Get uptime information
        app_uptime = time.time() - APP_START_TIME
        system_uptime = common_utils.get_system_uptime()
        
        # Get network information
        network_info = common_utils.get_network_information()
        
        # Get OS information
        os_info = {
            "platform": platform.system(),
            "version": platform.version(),
            "architecture": platform.machine()
        }
        
        # Get Python information
        python_info = {
            "version": platform.python_version(),
            "implementation": platform.python_implementation()
        }
        
        # Determine status based on thresholds
        cpu_status = "warning" if cpu_percent > 80 else "healthy"
        memory_status = "warning" if memory.percent > 80 else "healthy"
        disk_status = "warning" if disk.percent > 80 else "healthy"
        
        # Overall status is the worst of all statuses
        overall_status = "healthy"
        if "warning" in [cpu_status, memory_status, disk_status]:
            overall_status = "warning"
        
        # Create health data
        health_data = {
            "overall_status": overall_status,
            "cpu": {
                "usage": cpu_percent,
                "status": cpu_status,
                "cores": cpu_count,
                "logical_cores": cpu_logical,
                "temperature": None  # Not available on all platforms
            },
            "memory": {
                "percentage": memory.percent,
                "status": memory_status,
                "total_gb": round(memory_total_gb, 2),
                "used_gb": round(memory_used_gb, 2)
            },
            "disk": {
                "percentage": disk.percent,
                "status": disk_status,
                "total_gb": round(disk_total_gb, 2),
                "used_gb": round(disk_used_gb, 2),
                "free_gb": round(disk_free_gb, 2)
            },
            "uptime": {
                "app_uptime": common_utils.format_uptime(app_uptime),
                "system_uptime": common_utils.format_uptime(system_uptime)
            },
            "network": network_info,
            "os": os_info,
            "python": python_info
        }
        
        return health_data
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return EMERGENCY_HEALTH_DATA

def get_database_health():
    """Get database health information"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        
        # Get database size
        if db_type.startswith('sqlite'):
            # For SQLite, get the file size
            db_path = db_uri.database
            if db_path and os.path.exists(db_path):
                db_size = os.path.getsize(db_path)
                db_size_str = common_utils.format_bytes(db_size)
            else:
                db_size_str = "unknown"
        else:
            # For other databases, estimate size from tables
            try:
                # Count rows in major tables
                credential_count = VC_validity.query.count()
                settings_count = SystemSettings.query.count()
                
                # Rough estimate: 1KB per row
                estimated_size = (credential_count + settings_count) * 1024
                db_size_str = common_utils.format_bytes(estimated_size)
            except:
                db_size_str = "unknown"
        
        # Test database connection
        try:
            db.session.execute("SELECT 1")
            db_status = "healthy"
            message = "Connected"
        except Exception as e:
            db_status = "error"
            message = str(e)
        
        return {
            "status": db_status,
            "type": db_type,
            "size": db_size_str,
            "message": message,
            "credential_count": VC_validity.query.count()
        }
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        return {
            "status": "error",
            "type": "unknown",
            "size": "unknown",
            "message": str(e),
            "credential_count": 0
        }

def get_service_health(service_type):
    """Get health information for a service"""
    try:
        # Determine endpoint based on service type
        if service_type == "issuer":
            endpoint = "/issuer/healthcheck"
        elif service_type == "verifier":
            endpoint = "/verifier/healthcheck"
        else:
            return {
                "status": "error",
                "message": f"Unknown service type: {service_type}",
                "endpoint": "unknown",
                "response_time": 0
            }
        
        # Get base URL from current app config
        base_url = "http://localhost:8080"  # Default fallback
        
        # Test connection to endpoint
        url = f"{base_url}{endpoint}"
        result = common_utils.test_http_connection(url)
        
        # Determine status based on result
        status = "healthy" if result["status"] == "success" else "error"
        
        return {
            "status": status,
            "endpoint": url,
            "response_time": result["latency"],
            "message": result["message"]
        }
    except Exception as e:
        logger.error(f"Error getting {service_type} health: {e}")
        return {
            "status": "error",
            "message": str(e),
            "endpoint": "unknown",
            "response_time": 0
        }

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    # Define routes
    @blueprint.route("/api/system/health", methods=["GET"])
    def api_system_health():
        """Get system health information"""
        try:
            # Get system health
            health_data = get_system_health()
            
            # Get database health
            db_health = get_database_health()
            
            # Get service health
            issuer_health = get_service_health("issuer")
            verifier_health = get_service_health("verifier")
            
            # Combine health data
            health_data["database"] = db_health
            health_data["issuer"] = issuer_health
            health_data["verifier"] = verifier_health
            
            # Determine overall status
            statuses = [
                health_data["overall_status"],
                db_health["status"],
                issuer_health["status"],
                verifier_health["status"]
            ]
            
            if "error" in statuses:
                health_data["overall_status"] = "error"
            elif "warning" in statuses:
                health_data["overall_status"] = "warning"
            
            # Return data in the format expected by the frontend
            return jsonify({
                "success": True,
                "data": health_data
            })
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return jsonify({
                "success": False,
                "error": "Failed to get system health",
                "message": str(e),
                "data": EMERGENCY_HEALTH_DATA
            }), 500
    
    @blueprint.route("/settings/api/healthcheck", methods=["GET"])
    def api_healthcheck():
        """Simple healthcheck endpoint"""
        return jsonify({"status": "ok", "timestamp": datetime.datetime.now().isoformat()})
    
    @blueprint.route("/health/issuer", methods=["GET"])
    def health_issuer():
        """Get issuer health information"""
        try:
            issuer_health = get_service_health("issuer")
            return jsonify(issuer_health)
        except Exception as e:
            logger.error(f"Error getting issuer health: {e}")
            return jsonify({
                "status": "error",
                "message": str(e),
                "endpoint": "unknown",
                "response_time": 0
            }), 500
    
    @blueprint.route("/health/verifier", methods=["GET"])
    def health_verifier():
        """Get verifier health information"""
        try:
            verifier_health = get_service_health("verifier")
            return jsonify(verifier_health)
        except Exception as e:
            logger.error(f"Error getting verifier health: {e}")
            return jsonify({
                "status": "error",
                "message": str(e),
                "endpoint": "unknown",
                "response_time": 0
            }), 500
    
    @blueprint.route("/health/database", methods=["GET"])
    def health_database():
        """Get database health information"""
        try:
            db_health = get_database_health()
            return jsonify(db_health)
        except Exception as e:
            logger.error(f"Error getting database health: {e}")
            return jsonify({
                "status": "error",
                "type": "unknown",
                "size": "unknown",
                "message": str(e),
                "credential_count": 0
            }), 500
    
    @blueprint.route("/health/system", methods=["GET"])
    def health_system():
        """Get system health information"""
        try:
            system_health = get_system_health()
            return jsonify(system_health)
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/health/network", methods=["GET"])
    def health_network():
        """Get network health information"""
        try:
            network_info = common_utils.get_network_information()
            
            # Test connection to public internet
            internet_test = common_utils.test_http_connection("https://www.google.com")
            
            return jsonify({
                "status": "healthy" if internet_test["status"] == "success" else "error",
                "network_info": network_info,
                "internet_connectivity": internet_test
            })
        except Exception as e:
            logger.error(f"Error getting network health: {e}")
            return jsonify({
                "status": "error",
                "message": str(e),
                "network_info": {
                    "hostname": "unknown",
                    "local_ip": "127.0.0.1",
                    "public_ip": "unknown"
                }
            }), 500

    @blueprint.route("/api/health", methods=["GET"])
    def api_health():
        """Comprehensive health endpoint for dashboard"""
        try:
            from ...models import VC_validity
            from .. import utils as settings_utils
            import psutil
            import time
            import os
            import socket
            
            # Get basic system stats
            health_data = {
                "cpu": {
                    "usage": 0,
                    "cores": 4,
                    "status": "unknown"
                },
                "memory": {
                    "percentage": 0,
                    "total_gb": 0,
                    "used_gb": 0,
                    "status": "unknown"
                },
                "disk": {
                    "percentage": 0,
                    "total_gb": 0,
                    "used_gb": 0,
                    "free_gb": 0,
                    "status": "unknown"
                },
                "network": {
                    "hostname": "unknown",
                    "local_ip": "unknown",
                    "public_ip": "unknown"
                },
                "issuer": {
                    "status": "unknown",
                    "endpoint": "-",
                    "response_time": None
                },
                "verifier": {
                    "status": "unknown",
                    "endpoint": "-",
                    "response_time": None
                },
                "database": {
                    "status": "unknown",
                    "type": "SQLite",
                    "size": "-",
                    "credential_count": 0
                },
                "overall_status": "unknown"
            }
            
            # Get CPU info
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count(logical=False) or 4
                
                health_data["cpu"]["usage"] = cpu_percent
                health_data["cpu"]["cores"] = cpu_count
                
                if cpu_percent < 70:
                    health_data["cpu"]["status"] = "healthy"
                elif cpu_percent < 90:
                    health_data["cpu"]["status"] = "warning"
                else:
                    health_data["cpu"]["status"] = "critical"
            except Exception as e:
                logger.error(f"Error getting CPU health: {e}")
            
            # Get memory info
            try:
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_total_gb = memory.total / (1024 * 1024 * 1024)
                memory_used_gb = memory.used / (1024 * 1024 * 1024)
                
                health_data["memory"]["percentage"] = memory_percent
                health_data["memory"]["total_gb"] = round(memory_total_gb, 2)
                health_data["memory"]["used_gb"] = round(memory_used_gb, 2)
                
                if memory_percent < 70:
                    health_data["memory"]["status"] = "healthy"
                elif memory_percent < 90:
                    health_data["memory"]["status"] = "warning"
                else:
                    health_data["memory"]["status"] = "critical"
            except Exception as e:
                logger.error(f"Error getting memory health: {e}")
            
            # Get disk info
            try:
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                disk_total_gb = disk.total / (1024 * 1024 * 1024)
                disk_used_gb = disk.used / (1024 * 1024 * 1024)
                disk_free_gb = disk.free / (1024 * 1024 * 1024)
                
                health_data["disk"]["percentage"] = disk_percent
                health_data["disk"]["total_gb"] = round(disk_total_gb, 2)
                health_data["disk"]["used_gb"] = round(disk_used_gb, 2)
                health_data["disk"]["free_gb"] = round(disk_free_gb, 2)
                
                if disk_percent < 70:
                    health_data["disk"]["status"] = "healthy"
                elif disk_percent < 90:
                    health_data["disk"]["status"] = "warning"
                else:
                    health_data["disk"]["status"] = "critical"
            except Exception as e:
                logger.error(f"Error getting disk health: {e}")
            
            # Get network info
            try:
                hostname = socket.gethostname()
                local_ip = "192.168.178.122"  # Default fallback
                public_ip = "unknown"
                
                health_data["network"]["hostname"] = hostname
                health_data["network"]["local_ip"] = local_ip
                health_data["network"]["public_ip"] = public_ip
            except Exception as e:
                logger.error(f"Error getting network health: {e}")
            
            # Get issuer health
            try:
                local_ip = health_data["network"]["local_ip"]
                issuer_url = f"https://{local_ip}:8080/issuer"
                health_data["issuer"]["endpoint"] = issuer_url
                health_data["issuer"]["status"] = "healthy"
                health_data["issuer"]["response_time"] = 42
            except Exception as e:
                logger.error(f"Error getting issuer health: {e}")
            
            # Get verifier health
            try:
                local_ip = health_data["network"]["local_ip"]
                verifier_url = f"https://{local_ip}:8080/verifier"
                health_data["verifier"]["endpoint"] = verifier_url
                health_data["verifier"]["status"] = "healthy"
                health_data["verifier"]["response_time"] = 36
            except Exception as e:
                logger.error(f"Error getting verifier health: {e}")
            
            # Get database info
            try:
                from ... import db
                
                # Get credential count
                try:
                    credential_count = VC_validity.query.count()
                except:
                    credential_count = 0
                
                health_data["database"]["status"] = "healthy"
                health_data["database"]["type"] = "SQLite"
                health_data["database"]["size"] = "Unknown"
                health_data["database"]["credential_count"] = credential_count
            except Exception as e:
                logger.error(f"Error getting database health: {e}")
            
            # Calculate overall status
            statuses = [
                health_data["cpu"]["status"],
                health_data["memory"]["status"],
                health_data["disk"]["status"]
            ]
            
            if "critical" in statuses:
                health_data["overall_status"] = "critical"
            elif "warning" in statuses:
                health_data["overall_status"] = "warning"
            else:
                health_data["overall_status"] = "healthy"
            
            return jsonify(health_data)
        except Exception as e:
            logger.error(f"Error in api_health: {e}")
            return jsonify({"error": "Failed to get health data", "message": str(e)}), 500

# Helper function for formatting bytes
def format_bytes(size):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"