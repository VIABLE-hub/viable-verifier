from flask import request, jsonify, render_template, send_file
import logging
import json
import os
import datetime
from werkzeug.utils import secure_filename
from ... import db
from ...models import SystemSettings
from . import utils as db_utils

logger = logging.getLogger(__name__)

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    # Define routes
    @blueprint.route("/settings/api/database", methods=["GET"])
    def api_database_info():
        """Get database information"""
        try:
            # Get database information
            db_info = db_utils.get_database_info()
            return jsonify({"status": "success", "data": db_info})
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @blueprint.route("/api/database/status", methods=["GET"])
    def api_database_status():
        """Get database status"""
        try:
            # Get database information
            db_info = db_utils.get_database_info()
            
            # Get last backup time
            success, backups = db_utils.list_database_backups()
            last_backup = backups[0] if success and backups else None
            
            # Create response
            response = {
                "status": "success",
                "database": db_info,
                "last_backup": last_backup
            }
            
            return jsonify(response)
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e),
                "database": {
                    "type": "unknown",
                    "size": "unknown"
                },
                "last_backup": None
            }), 500
    
    @blueprint.route("/api/database/backup/create", methods=["POST"])
    def api_database_backup_create():
        """Create a database backup"""
        try:
            # Get backup parameters
            data = request.json or {}
            backup_type = data.get("type", "manual")
            notes = data.get("notes")
            
            # Create backup
            success, result = db_utils.create_database_backup(backup_type=backup_type, notes=notes)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "Database backup created successfully",
                    "backup": result
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/backup/list", methods=["GET"])
    def api_database_backup_list():
        """List database backups"""
        try:
            # Get backups
            success, backups = db_utils.list_database_backups()
            
            if success:
                return jsonify({
                    "status": "success",
                    "backups": backups
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": backups
                }), 500
        except Exception as e:
            logger.error(f"Error listing database backups: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/backup/restore", methods=["POST"])
    def api_database_backup_restore():
        """Restore a database backup"""
        try:
            # Get backup filename
            data = request.json
            if not data or "filename" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Backup filename is required"
                }), 400
            
            backup_filename = data["filename"]
            
            # Restore backup
            success, result = db_utils.restore_database_backup(backup_filename)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "Database backup restored successfully",
                    "restore": result
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error restoring database backup: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/backup/delete", methods=["POST"])
    def api_database_backup_delete():
        """Delete a database backup"""
        try:
            # Get backup filename
            data = request.json
            if not data or "filename" not in data:
                return jsonify({
                    "status": "error",
                    "message": "Backup filename is required"
                }), 400
            
            backup_filename = data["filename"]
            
            # Delete backup
            success, result = db_utils.delete_database_backup(backup_filename)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "Database backup deleted successfully",
                    "delete": result
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error deleting database backup: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/export/sql", methods=["POST"])
    def api_database_export_sql():
        """Export database to SQL file"""
        try:
            # Export database
            success, result = db_utils.export_database_sql()
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "Database exported successfully",
                    "export": result
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/import/sql", methods=["POST"])
    def api_database_import_sql():
        """Import database from SQL file"""
        try:
            # Check if file was uploaded
            if 'file' not in request.files:
                return jsonify({
                    "status": "error",
                    "message": "No file part"
                }), 400
            
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    "status": "error",
                    "message": "No selected file"
                }), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(os.path.dirname(db.engine.url.database), "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            
            # Import database
            success, result = db_utils.import_database_sql(filepath)
            
            # Clean up uploaded file
            try:
                os.remove(filepath)
            except:
                pass
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": "Database imported successfully",
                    "import": result
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error importing database: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/backup/download", methods=["GET"])
    def api_database_backup_download():
        """Download a database backup"""
        try:
            # Get backup filename
            filename = request.args.get("filename")
            if not filename:
                return jsonify({
                    "status": "error",
                    "message": "Backup filename is required"
                }), 400
            
            # Get backup file
            success, result = db_utils.get_database_backup(filename)
            
            if success:
                # Send file
                return send_file(
                    result["path"],
                    as_attachment=True,
                    download_name=filename,
                    mimetype="application/octet-stream"
                )
            else:
                return jsonify({
                    "status": "error",
                    "message": result
                }), 500
        except Exception as e:
            logger.error(f"Error downloading database backup: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/api/database/export", methods=["GET"])
    def api_database_export_redirect():
        """Redirect to export database page"""
        try:
            # Export database
            return api_database_export_sql()
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    @blueprint.route("/settings/database", methods=["GET"])
    def settings_database_get():
        """Get database settings page"""
        try:
            # Get database information
            db_info = db_utils.get_database_info()
            
            # Get backups
            success, backups = db_utils.list_database_backups()
            
            # Render template
            return render_template(
                "settings/database.html",
                db_info=db_info,
                backups=backups if success else []
            )
        except Exception as e:
            logger.error(f"Error getting database settings page: {e}")
            return render_template(
                "settings/database.html",
                db_info={},
                backups=[],
                error=str(e)
            )
