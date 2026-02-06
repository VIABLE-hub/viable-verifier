import logging
import os
import shutil
import datetime
import sqlite3
import json
import time
from ... import db
from .. import utils as common_utils

logger = logging.getLogger(__name__)

def get_database_info():
    """Get database information"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        # Get database size
        if db_type.startswith('sqlite') and db_path and os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            db_size_str = common_utils.format_bytes(db_size)
            
            # Get creation and modification time
            db_ctime = os.path.getctime(db_path)
            db_mtime = os.path.getmtime(db_path)
            
            # Format times
            db_ctime_str = common_utils.format_datetime(datetime.datetime.fromtimestamp(db_ctime))
            db_mtime_str = common_utils.format_datetime(datetime.datetime.fromtimestamp(db_mtime))
            
            # Get table information
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get list of tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get row counts for each table
                table_info = {}
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        table_info[table] = count
                    except:
                        table_info[table] = "error"
                
                conn.close()
            except Exception as e:
                logger.error(f"Error getting table information: {e}")
                tables = []
                table_info = {}
        else:
            db_size_str = "unknown"
            db_ctime_str = "unknown"
            db_mtime_str = "unknown"
            tables = []
            table_info = {}
        
        return {
            "type": db_type,
            "path": db_path,
            "size": db_size_str,
            "created": db_ctime_str,
            "modified": db_mtime_str,
            "tables": tables,
            "table_info": table_info
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        return {
            "type": "unknown",
            "path": "unknown",
            "size": "unknown",
            "created": "unknown",
            "modified": "unknown",
            "tables": [],
            "table_info": {}
        }

def create_database_backup(backup_dir=None, backup_type="manual", notes=None):
    """Create a backup of the database"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        if not db_type.startswith('sqlite') or not db_path or not os.path.exists(db_path):
            return False, "Database not supported for backup"
        
        # Create backup directory if not provided
        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        
        # Create directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = int(time.time())
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Create backup metadata
        metadata = {
            "timestamp": timestamp,
            "datetime": datetime.datetime.now().isoformat(),
            "type": backup_type,
            "notes": notes,
            "original_path": db_path,
            "backup_path": backup_path
        }
        
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Save metadata
        metadata_path = backup_path + ".json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return True, {
            "filename": backup_filename,
            "path": backup_path,
            "size": common_utils.format_bytes(os.path.getsize(backup_path)),
            "timestamp": timestamp,
            "datetime": metadata["datetime"],
            "type": backup_type,
            "notes": notes
        }
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        return False, str(e)

def list_database_backups(backup_dir=None):
    """List database backups"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        # Use default backup directory if not provided
        if not backup_dir:
            if db_path:
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            else:
                return False, "Database path not found"
        
        # Check if directory exists
        if not os.path.exists(backup_dir):
            return True, []
        
        # Get list of backup files
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                backup_path = os.path.join(backup_dir, filename)
                metadata_path = backup_path + ".json"
                
                # Get file information
                file_size = os.path.getsize(backup_path)
                file_mtime = os.path.getmtime(backup_path)
                
                # Get metadata if available
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                # Create backup info
                backup_info = {
                    "filename": filename,
                    "path": backup_path,
                    "size": common_utils.format_bytes(file_size),
                    "timestamp": metadata.get("timestamp", int(file_mtime)),
                    "datetime": metadata.get("datetime", common_utils.format_datetime(datetime.datetime.fromtimestamp(file_mtime))),
                    "type": metadata.get("type", "unknown"),
                    "notes": metadata.get("notes", None)
                }
                
                backups.append(backup_info)
        
        # Sort backups by timestamp (newest first)
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return True, backups
    except Exception as e:
        logger.error(f"Error listing database backups: {e}")
        return False, str(e)

def restore_database_backup(backup_filename, backup_dir=None):
    """Restore a database backup"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        if not db_type.startswith('sqlite') or not db_path:
            return False, "Database not supported for restore"
        
        # Use default backup directory if not provided
        if not backup_dir:
            backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        
        # Check if backup file exists
        backup_path = os.path.join(backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            return False, f"Backup file not found: {backup_filename}"
        
        # Create a backup of the current database
        current_backup_dir = os.path.join(backup_dir, "restore_backups")
        os.makedirs(current_backup_dir, exist_ok=True)
        
        timestamp = int(time.time())
        current_backup_filename = f"pre_restore_{timestamp}.db"
        current_backup_path = os.path.join(current_backup_dir, current_backup_filename)
        
        # Copy current database
        shutil.copy2(db_path, current_backup_path)
        
        # Close database connection
        db.session.close()
        db.engine.dispose()
        
        # Restore backup
        shutil.copy2(backup_path, db_path)
        
        return True, {
            "original_backup": backup_filename,
            "current_backup": current_backup_filename,
            "timestamp": timestamp,
            "datetime": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error restoring database backup: {e}")
        return False, str(e)

def delete_database_backup(backup_filename, backup_dir=None):
    """Delete a database backup"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        # Use default backup directory if not provided
        if not backup_dir:
            if db_path:
                backup_dir = os.path.join(os.path.dirname(db_path), "backups")
            else:
                return False, "Database path not found"
        
        # Check if backup file exists
        backup_path = os.path.join(backup_dir, backup_filename)
        if not os.path.exists(backup_path):
            return False, f"Backup file not found: {backup_filename}"
        
        # Delete backup file
        os.remove(backup_path)
        
        # Delete metadata file if it exists
        metadata_path = backup_path + ".json"
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        
        return True, {
            "filename": backup_filename,
            "path": backup_path,
            "deleted": True
        }
    except Exception as e:
        logger.error(f"Error deleting database backup: {e}")
        return False, str(e)

def export_database_sql(export_path=None):
    """Export database to SQL file"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        if not db_type.startswith('sqlite') or not db_path:
            return False, "Database not supported for export"
        
        # Create export directory if not provided
        if not export_path:
            export_dir = os.path.join(os.path.dirname(db_path), "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate export filename
            timestamp = int(time.time())
            export_filename = f"export_{timestamp}.sql"
            export_path = os.path.join(export_dir, export_filename)
        
        # Export database to SQL
        conn = sqlite3.connect(db_path)
        with open(export_path, 'w') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        conn.close()
        
        return True, {
            "path": export_path,
            "size": common_utils.format_bytes(os.path.getsize(export_path)),
            "timestamp": int(time.time()),
            "datetime": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error exporting database to SQL: {e}")
        return False, str(e)

def import_database_sql(sql_file):
    """Import database from SQL file"""
    try:
        # Get database information
        db_uri = db.engine.url
        db_type = db_uri.drivername
        db_path = db_uri.database if hasattr(db_uri, 'database') else None
        
        if not db_type.startswith('sqlite') or not db_path:
            return False, "Database not supported for import"
        
        # Check if SQL file exists
        if not os.path.exists(sql_file):
            return False, f"SQL file not found: {sql_file}"
        
        # Create a backup of the current database
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = int(time.time())
        backup_filename = f"pre_import_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Copy current database
        shutil.copy2(db_path, backup_path)
        
        # Close database connection
        db.session.close()
        db.engine.dispose()
        
        # Create new database
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Import SQL file
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        
        return True, {
            "backup": backup_filename,
            "backup_path": backup_path,
            "imported": sql_file,
            "timestamp": timestamp,
            "datetime": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error importing database from SQL: {e}")
        return False, str(e)
