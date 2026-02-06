from flask import jsonify, send_file, current_app, request
import os
import logging
import shutil
import sqlite3
import time
import datetime
import hashlib
from werkzeug.utils import secure_filename

from .. import settings
from ..utils import format_bytes

# Initialize logger for database backup module
logger = logging.getLogger(__name__)

def get_last_backup_time():
    """
    Get the time of the last database backup
    """
    try:
        backups_dir = get_backups_dir()
        if not os.path.exists(backups_dir):
            return None
            
        # List all backup files and get the most recent one
        backup_files = [f for f in os.listdir(backups_dir) if f.endswith('.db')]
        
        if not backup_files:
            return None
            
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda f: os.path.getmtime(os.path.join(backups_dir, f)), reverse=True)
        
        # Get the most recent backup file
        latest_backup = backup_files[0]
        backup_path = os.path.join(backups_dir, latest_backup)
        
        # Get the backup timestamp
        backup_time = os.path.getmtime(backup_path)
        
        return datetime.datetime.fromtimestamp(backup_time).isoformat()
    except Exception as e:
        logger.error(f"Error getting last backup time: {e}")
        return None

def get_backups_dir():
    """
    Get the directory where database backups are stored
    """
    instance_path = current_app.instance_path
    backups_dir = os.path.join(instance_path, 'backups')
    
    # Create the backups directory if it doesn't exist
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)
        
    return backups_dir

def api_database_backup():
    """
    Create a database backup
    """
    return api_database_backup_create()

def api_list_database_backups():
    """
    List all database backups
    """
    try:
        backups = list_database_backups()
        return jsonify({"backups": backups}), 200
    except Exception as e:
        logger.error(f"Error listing database backups: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_download_database_backup():
    """
    Download a database backup
    """
    try:
        filename = request.args.get('filename')
        if not filename:
            return jsonify({"status": "error", "message": "Missing filename parameter"}), 400
            
        # Ensure the filename is secure and valid
        filename = secure_filename(filename)
        
        # Get the full path to the backup file
        backups_dir = get_backups_dir()
        backup_path = os.path.join(backups_dir, filename)
        
        # Check if the file exists
        if not os.path.exists(backup_path):
            return jsonify({"status": "error", "message": f"Backup file not found: {filename}"}), 404
            
        # Send the file
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Error downloading database backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_restore_database_backup(filename):
    """
    Restore a database backup
    """
    try:
        # Ensure the filename is secure and valid
        filename = secure_filename(filename)
        
        # Get the full path to the backup file
        backups_dir = get_backups_dir()
        backup_path = os.path.join(backups_dir, filename)
        
        # Check if the file exists
        if not os.path.exists(backup_path):
            return jsonify({"status": "error", "message": f"Backup file not found: {filename}"}), 404
            
        # Get the path to the current database file
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri.startswith('sqlite:///'):
            return jsonify({"status": "error", "message": "Only SQLite databases are supported for restore"}), 400
            
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # If it's a relative path, make it absolute from the instance folder
            db_path = os.path.join(current_app.instance_path, db_path)
            
        # Create a backup of the current database before restoring
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        temp_backup_filename = f"pre_restore_backup_{timestamp}.db"
        temp_backup_path = os.path.join(backups_dir, temp_backup_filename)
        
        # Check if the database file exists
        if os.path.exists(db_path):
            shutil.copy2(db_path, temp_backup_path)
            logger.info(f"Created backup of current database at {temp_backup_path}")
            
        # Restore the backup
        shutil.copy2(backup_path, db_path)
        
        logger.info(f"Restored database from backup: {filename}")
        return jsonify({
            "status": "success",
            "message": f"Database restored from backup: {filename}",
            "backup_created": temp_backup_filename
        }), 200
    except Exception as e:
        logger.error(f"Error restoring database backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_database_reset():
    """
    Reset the database (dangerous operation)
    """
    try:
        # Verify confirmation code
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        confirmation_code = data.get('confirmation_code', '')
        
        expected_code = "RESET-CONFIRM"
        if confirmation_code != expected_code:
            return jsonify({"status": "error", "message": f"Invalid confirmation code, must be '{expected_code}'"}), 400
            
        # Get the path to the current database file
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri.startswith('sqlite:///'):
            return jsonify({"status": "error", "message": "Only SQLite databases are supported for reset"}), 400
            
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # If it's a relative path, make it absolute from the instance folder
            db_path = os.path.join(current_app.instance_path, db_path)
            
        # Create a backup before resetting
        backups_dir = get_backups_dir()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"pre_reset_backup_{timestamp}.db"
        backup_path = os.path.join(backups_dir, backup_filename)
        
        # Check if the database file exists
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created backup of database before reset at {backup_path}")
            
            # Reset the database by creating a new empty file
            with open(db_path, 'w') as f:
                pass
            
            logger.info("Database has been reset")
            return jsonify({
                "status": "success",
                "message": "Database has been reset",
                "backup_created": backup_filename
            }), 200
        else:
            return jsonify({"status": "error", "message": "Database file not found"}), 404
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def list_database_backups():
    """
    List all database backups with detailed information
    """
    try:
        backups_dir = get_backups_dir()
        if not os.path.exists(backups_dir):
            return []
            
        # List all backup files
        backup_files = [f for f in os.listdir(backups_dir) if f.endswith('.db')]
        
        backups = []
        total_size = 0
        
        for filename in backup_files:
            backup_path = os.path.join(backups_dir, filename)
            
            # Get file information
            stats = os.stat(backup_path)
            size = stats.st_size
            modified_time = stats.st_mtime
            
            # Parse timestamp from filename if it follows the format: backup_YYYY-MM-DD_HH-MM-SS.db
            timestamp = None
            try:
                if filename.startswith('backup_'):
                    date_part = filename[len('backup_'):-3]  # Remove 'backup_' prefix and '.db' suffix
                    timestamp = datetime.datetime.strptime(date_part, '%Y-%m-%d_%H-%M-%S')
            except:
                # If parsing fails, use the file modified time
                timestamp = datetime.datetime.fromtimestamp(modified_time)
            
            # If timestamp is still None, use the file modified time
            if not timestamp:
                timestamp = datetime.datetime.fromtimestamp(modified_time)
                
            # Calculate age in days
            age_days = (datetime.datetime.now() - timestamp).days
            
            # Calculate file hash
            file_hash = calculate_file_hash(backup_path)
            
            # Add to backups list
            backups.append({
                "filename": filename,
                "size": size,
                "size_formatted": format_bytes(size),
                "timestamp": timestamp.isoformat(),
                "age_days": age_days,
                "hash": file_hash
            })
            
            total_size += size
            
        # Sort backups by timestamp (newest first)
        backups.sort(key=lambda b: b["timestamp"], reverse=True)
        
        # Add total size
        result = {
            "backups": backups,
            "total_count": len(backups),
            "total_size": total_size,
            "total_size_formatted": format_bytes(total_size)
        }
        
        return result
    except Exception as e:
        logger.error(f"Error listing database backups: {e}")
        return {"backups": [], "total_count": 0, "total_size": 0, "total_size_formatted": "0 B"}

def api_database_backup_create():
    """
    Create a database backup
    """
    try:
        # Get the path to the current database file
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri.startswith('sqlite:///'):
            return jsonify({"status": "error", "message": "Only SQLite databases are supported for backup"}), 400
            
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # If it's a relative path, make it absolute from the instance folder
            db_path = os.path.join(current_app.instance_path, db_path)
            
        # Check if the database file exists
        if not os.path.exists(db_path):
            return jsonify({"status": "error", "message": "Database file not found"}), 404
            
        # Create a backup
        backups_dir = get_backups_dir()
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backups_dir, backup_filename)
        
        # Copy the database file
        shutil.copy2(db_path, backup_path)
        
        # Get backup size
        backup_size = os.path.getsize(backup_path)
        backup_size_formatted = format_bytes(backup_size)
        
        logger.info(f"Created database backup: {backup_filename} ({backup_size_formatted})")
        return jsonify({
            "status": "success",
            "message": f"Database backup created: {backup_filename} ({backup_size_formatted})",
            "filename": backup_filename,
            "size": backup_size,
            "size_formatted": backup_size_formatted,
            "timestamp": timestamp
        }), 200
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_database_backup_restore():
    """
    Restore a database backup
    """
    try:
        # Get the backup filename from the request
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        filename = data.get('filename')
        confirmation_code = data.get('confirmation_code', '')
        
        if not filename:
            return jsonify({"status": "error", "message": "Missing filename parameter"}), 400
            
        # Verify confirmation code
        expected_code = "RESTORE-CONFIRM"
        if confirmation_code != expected_code:
            return jsonify({"status": "error", "message": f"Invalid confirmation code, must be '{expected_code}'"}), 400
            
        # Call the restore function
        return api_restore_database_backup(filename)
    except Exception as e:
        logger.error(f"Error restoring database backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def api_database_backup_delete():
    """
    Delete a database backup
    """
    try:
        # Get the backup filename from the request
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
            
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({"status": "error", "message": "Missing filename parameter"}), 400
            
        # Ensure the filename is secure and valid
        filename = secure_filename(filename)
        
        # Get the full path to the backup file
        backups_dir = get_backups_dir()
        backup_path = os.path.join(backups_dir, filename)
        
        # Check if the file exists
        if not os.path.exists(backup_path):
            return jsonify({"status": "error", "message": f"Backup file not found: {filename}"}), 404
            
        # Delete the file
        os.remove(backup_path)
        
        logger.info(f"Deleted database backup: {filename}")
        return jsonify({
            "status": "success",
            "message": f"Database backup deleted: {filename}"
        }), 200
    except Exception as e:
        logger.error(f"Error deleting database backup: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def calculate_file_hash(file_path):
    """
    Calculate SHA-256 hash of a file
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating file hash: {e}")
        return "unknown"

def api_database_backup_download():
    """
    Download a database backup
    """
    return api_download_database_backup()

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/database/backup", methods=["POST"])
    def bp_api_database_backup():
        return api_database_backup()
    
    @blueprint.route("/settings/api/database/backups", methods=["GET"])
    def bp_api_list_database_backups():
        return api_list_database_backups()
    
    @blueprint.route("/settings/api/database/download-backup", methods=["GET"])
    def bp_api_download_database_backup():
        return api_download_database_backup()
    
    @blueprint.route("/settings/api/database/restore/<filename>", methods=["POST"])
    def bp_api_restore_database_backup(filename):
        return api_restore_database_backup(filename)
    
    @blueprint.route("/settings/api/database/reset", methods=["POST"])
    def bp_api_database_reset():
        return api_database_reset()
    
    @blueprint.route('/api/database/backup/list')
    def bp_list_database_backups():
        return jsonify(list_database_backups())
    
    @blueprint.route('/api/database/backup/create', methods=['POST'])
    def bp_api_database_backup_create():
        return api_database_backup_create()
    
    @blueprint.route('/api/database/backup/restore', methods=['POST'])
    def bp_api_database_backup_restore():
        return api_database_backup_restore()
    
    @blueprint.route('/api/database/backup/delete', methods=['POST'])
    def bp_api_database_backup_delete():
        return api_database_backup_delete()
    
    @blueprint.route("/api/database/backup/download", methods=["GET"])
    def bp_api_database_backup_download():
        return api_database_backup_download() 