from flask import Blueprint, jsonify, current_app
import platform
import socket
import sys
import psutil
import os
from sqlalchemy import text
from . import db

system_bp = Blueprint('system_api', __name__)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@system_bp.route('/health')
def system_health():
    try:
        # Network Info
        hostname = socket.gethostname()
        local_ip = get_local_ip()
        
        try:
            # Simple check for public IP via external service or just return None/Scanning
            # For privacy/speed, we might skip external call or use a timeout
            public_ip = "Checking..." 
        except:
            public_ip = "Unknown"

        # Platform Info
        uname = platform.uname()
        
        # Database Info
        db_status = "unknown"
        try:
            # Check DB connection
            db.session.execute(text("SELECT 1"))
            db_status = "connected"
        except:
            db_status = "error"
            
        # Disk & Memory (using psutil) - simplified
        disk = psutil.disk_usage('/')
        mem = psutil.virtual_memory()

        data = {
            "overall_status": "healthy" if db_status == "connected" else "warning",
            "network": {
                "hostname": hostname,
                "local_ip": local_ip,
                "public_ip": public_ip
            },
            "platform": {
                "system": uname.system,
                "release": uname.release,
                "machine": uname.machine,
                "processor": uname.processor
            },
            "python_env": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler()
            },
            "app": {
                "version": "1.0.0",
                "debug": current_app.debug
            },
            "database": {
                "status": db_status,
                "type": "SQLite", # Assuming SQLite based on __init__.py
                "path": "database.db"
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            },
            "memory": {
                "total": mem.total,
                "available": mem.available,
                "percent": mem.percent
            }
        }

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
