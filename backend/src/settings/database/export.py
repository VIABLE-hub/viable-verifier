from flask import jsonify, send_file, current_app, request
import os
import logging
import subprocess
import tempfile
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename

from ..utils import format_bytes
from .backup import get_backups_dir, api_database_backup_create

# Initialize logger for database export module
logger = logging.getLogger(__name__)

def api_database_export():
    """
    Export database to SQL file
    """
    try:
        # Create a temporary file for the SQL dump
        with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Get the path to the current database file
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri.startswith('sqlite:///'):
            return jsonify({"status": "error", "message": "Only SQLite databases are supported for export"}), 400
            
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # If it's a relative path, make it absolute from the instance folder
            db_path = os.path.join(current_app.instance_path, db_path)
            
        # Check if the database file exists
        if not os.path.exists(db_path):
            return jsonify({"status": "error", "message": "Database file not found"}), 404
            
        # Create SQL dump using sqlite3 CLI
        try:
            # Try to use the sqlite3 command-line tool
            process = subprocess.Popen(
                ['sqlite3', db_path, '.dump'],
                stdout=open(temp_path, 'w'),
                stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"sqlite3 command failed: {stderr.decode('utf-8')}")
                
            logger.info(f"Created SQL dump at {temp_path} using sqlite3 command")
        except:
            # Fallback to Python's sqlite3 module
            try:
                conn = sqlite3.connect(db_path)
                with open(temp_path, 'w') as f:
                    # Get schema
                    for line in conn.iterdump():
                        f.write('%s\n' % line)
                conn.close()
                logger.info(f"Created SQL dump at {temp_path} using Python sqlite3 module")
            except Exception as e:
                os.unlink(temp_path)
                logger.error(f"Error creating SQL dump: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        # Get file information
        stats = os.stat(temp_path)
        size = stats.st_size
        
        # Generate download filename
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        download_filename = f"export_{timestamp}.sql"
        
        # Send file as attachment
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='text/plain'
        )
    except Exception as e:
        logger.error(f"Error exporting database: {e}")
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({"status": "error", "message": str(e)}), 500

def api_database_import():
    """
    Import database from SQL file
    """
    try:
        # Check if the SQL file was uploaded
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
            
        if not file.filename.endswith('.sql'):
            return jsonify({"status": "error", "message": "Only SQL files are supported for import"}), 400
            
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
            
        # Get the path to the current database file
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if not db_uri.startswith('sqlite:///'):
            os.unlink(temp_path)
            return jsonify({"status": "error", "message": "Only SQLite databases are supported for import"}), 400
            
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # If it's a relative path, make it absolute from the instance folder
            db_path = os.path.join(current_app.instance_path, db_path)
            
        # Create a backup before importing
        backup_result = api_database_backup_create()
        backup_data = backup_result.json
        
        if backup_result.status_code != 200 or backup_data.get('status') != 'success':
            os.unlink(temp_path)
            return jsonify({
                "status": "error",
                "message": "Failed to create backup before import",
                "backup_error": backup_data.get('message', 'Unknown error')
            }), 500
            
        # Import the SQL file using sqlite3 CLI
        try:
            # Create a new empty database
            if os.path.exists(db_path):
                os.remove(db_path)
                
            # Create new database connection
            conn = sqlite3.connect(db_path)
            
            # Import the SQL file
            with open(temp_path, 'r') as f:
                # Read the SQL file line by line
                script = f.read()
                conn.executescript(script)
                
            conn.commit()
            conn.close()
            
            logger.info(f"Imported SQL dump from {temp_path}")
        except Exception as e:
            # Restore from backup if import fails
            try:
                backup_filename = backup_data.get('filename')
                backups_dir = get_backups_dir()
                backup_path = os.path.join(backups_dir, backup_filename)
                import shutil
                shutil.copy2(backup_path, db_path)
                logger.info(f"Restored database from backup after import failure: {backup_filename}")
            except:
                logger.error("Failed to restore database from backup after import failure")
                
            os.unlink(temp_path)
            logger.error(f"Error importing SQL dump: {e}")
            return jsonify({"status": "error", "message": f"Import failed: {str(e)}"}), 500
        
        # Clean up
        os.unlink(temp_path)
        
        return jsonify({
            "status": "success",
            "message": "Database imported successfully",
            "backup_created": backup_data.get('filename')
        }), 200
    except Exception as e:
        logger.error(f"Error importing database: {e}")
        # Clean up temporary file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        return jsonify({"status": "error", "message": str(e)}), 500

def api_database_export_sql():
    """
    Export database to SQL file (alias endpoint)
    """
    return api_database_export()

def api_database_import_sql():
    """
    Import database from SQL file (alias endpoint)
    """
    return api_database_import()

def api_database_export_redirect():
    """
    Export database to SQL file (alias endpoint)
    """
    return api_database_export()

def export_database_sql():
    """
    Export database to SQL file (alias endpoint)
    """
    return api_database_export()

def import_database_sql():
    """
    Import database from SQL file (alias endpoint)
    """
    return api_database_import()

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    @blueprint.route("/settings/api/database/export", methods=["GET", "POST"])
    def bp_api_database_export():
        return api_database_export()
    
    @blueprint.route("/settings/api/database/import", methods=["POST"])
    def bp_api_database_import():
        return api_database_import()
    
    @blueprint.route("/api/database/export/sql", methods=["POST"])
    def bp_api_database_export_sql():
        return api_database_export_sql()
    
    @blueprint.route("/api/database/import/sql", methods=["POST"])
    def bp_api_database_import_sql():
        return api_database_import_sql()
    
    @blueprint.route("/api/database/export", methods=["GET"])
    def bp_api_database_export_redirect():
        return api_database_export_redirect()
    
    @blueprint.route('/api/database/export/sql')
    def bp_export_database_sql():
        return export_database_sql()
    
    @blueprint.route('/api/database/import/sql', methods=['POST'])
    def bp_import_database_sql():
        return import_database_sql() 