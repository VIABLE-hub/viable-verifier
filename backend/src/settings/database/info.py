from flask import jsonify, current_app
import os
import logging
import sqlite3
from datetime import datetime

from ... import db
from ...models import VC_validity
from ..utils import format_bytes

# Initialize logger for database info module
logger = logging.getLogger(__name__)

def get_database_info():
    """
    Get comprehensive database information
    """
    try:
        # Get database file path
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if not os.path.isabs(db_path):
                # If it's a relative path, make it absolute from the instance folder
                db_path = os.path.join(current_app.instance_path, db_path)
        else:
            # For other database types (MySQL, PostgreSQL, etc.)
            db_path = None
        
        # Get file size if it's SQLite
        if db_path and os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_size_formatted = format_bytes(db_size)
        else:
            db_size = 0
            db_size_formatted = "0 B"
        
        # Get database type
        if 'sqlite' in db_uri.lower():
            db_type = "SQLite"
            db_version = sqlite3.sqlite_version
        elif 'mysql' in db_uri.lower():
            db_type = "MySQL"
            db_version = "Unknown"  # Would require a connection to get version
        elif 'postgresql' in db_uri.lower():
            db_type = "PostgreSQL"
            db_version = "Unknown"  # Would require a connection to get version
        else:
            db_type = "Unknown"
            db_version = "Unknown"
        
        # Get table count and record counts using SQLAlchemy
        try:
            # Get table names
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            table_count = len(table_names)
            
            # Get record counts
            record_counts = {}
            total_records = 0
            
            # Count records in VC_validity table
            vc_count = VC_validity.query.count()
            record_counts['vc_validity'] = vc_count
            total_records += vc_count
            
            # In a real implementation, you would count records in other tables as well
            
        except Exception as e:
            logger.warning(f"Error getting table information: {e}")
            table_count = 0
            record_counts = {}
            total_records = 0
        
        return {
            "db_type": db_type,
            "db_version": db_version,
            "db_path": db_path,
            "db_size": db_size,
            "size_formatted": db_size_formatted,
            "table_count": table_count,
            "record_count": total_records,
            "record_counts": record_counts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "db_type": "Unknown",
            "db_version": "Unknown",
            "db_path": None,
            "db_size": 0,
            "size_formatted": "0 B",
            "table_count": 0,
            "record_count": 0,
            "record_counts": {},
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def api_database_info():
    """
    Get database information
    """
    try:
        db_info = get_database_info()
        return jsonify(db_info), 200
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return jsonify({"error": str(e)}), 500

def get_database_status():
    """
    Get database status information
    """
    try:
        db_info = get_database_info()
        
        # Additional status information
        status = "healthy"
        message = "Database is operational"
        
        # Check for potential issues
        if db_info.get("db_size", 0) > 1024 * 1024 * 500:  # 500 MB
            status = "warning"
            message = "Database size is large (>500 MB)"
        
        # Get backup information
        from .backup import get_last_backup_time
        last_backup = get_last_backup_time()
        
        # Get credential count
        credential_count = db_info.get("record_counts", {}).get("vc_validity", 0)
        
        # Get health status using the health endpoint
        from ..health.services import get_database_health
        health_status = get_database_health().get("status", "unknown")
        
        return jsonify({
            "status": status,
            "health_status": health_status,
            "message": message,
            "type": db_info.get("db_type", "Unknown"),
            "version": db_info.get("db_version", "Unknown"),
            "size": db_info.get("size_formatted", "0 B"),
            "size_bytes": db_info.get("db_size", 0),
            "tables": db_info.get("table_count", 0),
            "records": db_info.get("record_count", 0),
            "credential_count": credential_count,
            "last_backup": last_backup,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "type": "Unknown",
            "version": "Unknown",
            "size": "0 B",
            "size_bytes": 0,
            "tables": 0,
            "records": 0,
            "credential_count": 0,
            "last_backup": None,
            "timestamp": datetime.now().isoformat()
        }), 200  # Return 200 even on error to avoid breaking UI

def api_database_status():
    """
    Get database status information (alias endpoint)
    """
    return get_database_status()

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/database", methods=["GET"])
    def bp_api_database_info():
        return api_database_info()
    
    @blueprint.route('/api/database/status')
    def bp_get_database_status():
        return get_database_status()
    
    @blueprint.route("/api/database/status", methods=["GET"])
    def bp_api_database_status():
        return api_database_status() 