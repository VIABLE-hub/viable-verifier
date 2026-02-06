from flask import jsonify, current_app
import psutil
import platform
import sys
import time
import logging
import os
import json
from datetime import datetime

from ..core import APP_START_TIME, EMERGENCY_SYSTEM_INFO
from ..utils import format_bytes, format_time_delta
from ...models import VC_validity

# Initialize logger for system health module
logger = logging.getLogger(__name__)

# Emergency fallback data
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

def api_system_info():
    """
    Get system information
    """
    try:
        # Get CPU information
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count(logical=False)
        cpu_logical_cores = psutil.cpu_count(logical=True)
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_usage = memory.used
        memory_total = memory.total
        memory_percentage = memory.percent
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_usage = disk.used
        disk_total = disk.total
        disk_free = disk.free
        disk_percentage = disk.percent
        
        # Get uptime information
        app_uptime = time.time() - APP_START_TIME
        system_boot_time = psutil.boot_time()
        system_uptime = time.time() - system_boot_time
        
        # Get credential count
        try:
            credential_count = VC_validity.query.count()
        except Exception as e:
            logger.error(f"Error getting credential count: {e}")
            credential_count = 0
        
        # Get OS information
        os_platform = platform.system()
        os_version = platform.version()
        os_architecture = platform.machine()
        
        # Get Python information
        python_version = sys.version.split(' ')[0]
        python_implementation = platform.python_implementation()
        
        # Get git commit hash if available
        git_commit = os.environ.get('GIT_COMMIT', 'unknown')
        
        # Format uptime
        app_uptime_formatted = format_time_delta(app_uptime)
        system_uptime_formatted = format_time_delta(system_uptime)
        
        # Format byte sizes
        memory_usage_formatted = format_bytes(memory_usage)
        memory_total_formatted = format_bytes(memory_total)
        disk_usage_formatted = format_bytes(disk_usage)
        disk_total_formatted = format_bytes(disk_total)
        disk_free_formatted = format_bytes(disk_free)
        
        # Get service status from health endpoints
        from .services import get_issuer_health, get_verifier_health
        issuer_status = get_issuer_health().get('status', 'unknown')
        verifier_status = get_verifier_health().get('status', 'unknown')

        return jsonify({
            "cpu": {
                "usage": cpu_usage,
                "cores": cpu_cores,
                "logical_cores": cpu_logical_cores,
                "temperature": None  # Not available on all platforms
            },
            "memory": {
                "percentage": memory_percentage,
                "usage": memory_usage,
                "usage_formatted": memory_usage_formatted,
                "total": memory_total,
                "total_formatted": memory_total_formatted,
                "available": memory_total - memory_usage
            },
            "disk": {
                "percentage": disk_percentage,
                "usage": disk_usage,
                "usage_formatted": disk_usage_formatted,
                "total": disk_total,
                "total_formatted": disk_total_formatted,
                "free": disk_free,
                "free_formatted": disk_free_formatted
            },
            "uptime": {
                "app_uptime": app_uptime_formatted,
                "app_uptime_seconds": int(app_uptime),
                "system_uptime": system_uptime_formatted,
                "system_uptime_seconds": int(system_uptime),
                "boot_time": datetime.fromtimestamp(system_boot_time).isoformat()
            },
            "database": {
                "credential_count": credential_count
            },
            "services": {
                "issuer_status": issuer_status,
                "verifier_status": verifier_status
            },
            "os": {
                "platform": os_platform,
                "version": os_version,
                "architecture": os_architecture
            },
            "python": {
                "version": python_version,
                "implementation": python_implementation
            },
            "git": {
                "commit": git_commit
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return jsonify(EMERGENCY_SYSTEM_INFO)

def api_system_health():
    """
    Get comprehensive system health status
    """
    try:
        # Get CPU information
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_cores = psutil.cpu_count(logical=False)
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_percentage = memory.percent
        memory_total_gb = round(memory.total / (1024 ** 3), 1)
        memory_used_gb = round(memory.used / (1024 ** 3), 1)
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_percentage = disk.percent
        disk_total_gb = round(disk.total / (1024 ** 3), 1)
        disk_used_gb = round(disk.used / (1024 ** 3), 1)
        disk_free_gb = round(disk.free / (1024 ** 3), 1)
        
        # Get uptime information
        app_uptime = time.time() - APP_START_TIME
        system_boot_time = psutil.boot_time()
        system_uptime = time.time() - system_boot_time
        
        # Format uptime
        app_uptime_formatted = format_time_delta(app_uptime)
        system_uptime_formatted = format_time_delta(system_uptime)
        
        # Get hostname and network information
        import socket
        hostname = socket.gethostname()
        
        # Get local IP
        from ..network.config import get_local_ip, get_public_ip
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        
        # Determine health status based on thresholds
        cpu_status = "healthy"
        if cpu_usage > 90:
            cpu_status = "critical"
        elif cpu_usage > 75:
            cpu_status = "warning"
            
        memory_status = "healthy"
        if memory_percentage > 90:
            memory_status = "critical"
        elif memory_percentage > 75:
            memory_status = "warning"
            
        disk_status = "healthy"
        if disk_percentage > 90:
            disk_status = "critical"
        elif disk_percentage > 75:
            disk_status = "warning"
            
        # Get service status
        from .services import get_issuer_health, get_verifier_health, get_websocket_health, get_sse_health, get_database_health
        issuer_health = get_issuer_health()
        verifier_health = get_verifier_health()
        websocket_health = get_websocket_health()
        sse_health = get_sse_health()
        database_health = get_database_health()
        
        # Determine overall status
        overall_status = "healthy"
        if any(status == "critical" for status in [cpu_status, memory_status, disk_status, 
                                                  issuer_health.get("status"), verifier_health.get("status"),
                                                  database_health.get("status")]):
            overall_status = "critical"
        elif any(status == "warning" for status in [cpu_status, memory_status, disk_status,
                                                   issuer_health.get("status"), verifier_health.get("status"),
                                                   database_health.get("status")]):
            overall_status = "warning"
        
        return jsonify({
            "overall_status": overall_status,
            "cpu": {
                "usage": cpu_usage,
                "status": cpu_status,
                "cores": cpu_cores,
                "temperature": None  # Not available on all platforms
            },
            "memory": {
                "percentage": memory_percentage,
                "status": memory_status,
                "total_gb": memory_total_gb,
                "used_gb": memory_used_gb
            },
            "disk": {
                "percentage": disk_percentage,
                "status": disk_status,
                "total_gb": disk_total_gb,
                "used_gb": disk_used_gb,
                "free_gb": disk_free_gb
            },
            "uptime": {
                "app_uptime": app_uptime_formatted,
                "system_uptime": system_uptime_formatted
            },
            "network": {
                "hostname": hostname,
                "local_ip": local_ip,
                "public_ip": public_ip
            },
            "issuer": issuer_health,
            "verifier": verifier_health,
            "database": database_health,
            "websocket": websocket_health,
            "sse": sse_health,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify(EMERGENCY_HEALTH_DATA)

def health_system():
    """
    Get system health status
    """
    return api_system_health()

def api_healthcheck():
    """
    Get basic health status of all services
    """
    try:
        # Get service status
        from .services import get_issuer_health, get_verifier_health, get_websocket_health, get_sse_health, get_database_health
        issuer_health = get_issuer_health()
        verifier_health = get_verifier_health()
        websocket_health = get_websocket_health()
        sse_health = get_sse_health()
        database_health = get_database_health()
        
        # Determine overall status
        overall_status = "healthy"
        if any(health.get("status") == "critical" for health in [issuer_health, verifier_health, database_health]):
            overall_status = "critical"
        elif any(health.get("status") == "warning" for health in [issuer_health, verifier_health, database_health]):
            overall_status = "warning"
            
        return jsonify({
            "status": overall_status,
            "services": {
                "issuer": issuer_health.get("status", "unknown"),
                "verifier": verifier_health.get("status", "unknown"),
                "database": database_health.get("status", "unknown"),
                "websocket": websocket_health.get("status", "unknown"),
                "sse": sse_health.get("status", "unknown")
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting healthcheck: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "services": {
                "issuer": "unknown",
                "verifier": "unknown",
                "database": "unknown",
                "websocket": "unknown",
                "sse": "unknown"
            }
        })

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/system", methods=["GET"])
    def bp_api_system_info():
        return api_system_info()
    
    @blueprint.route("/api/system/health", methods=["GET"])
    def bp_api_system_health():
        return api_system_health()
    
    @blueprint.route("/health/system", methods=["GET"])
    def bp_health_system():
        return health_system()
    
    @blueprint.route("/settings/api/healthcheck", methods=["GET"])
    def bp_api_healthcheck():
        return api_healthcheck() 