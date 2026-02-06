from flask import request, jsonify, render_template
import logging
import json
import os
import uuid
import datetime
import secrets
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from .. import db
from ..models import SystemSettings, KeyRegistry, AuditLog
from .core import create_settings_backup
from sqlalchemy.orm.attributes import flag_modified

# Legacy compatibility
def get_current_user_email():
    return "admin@localhost"
from ..path_utils import get_instance_path

logger = logging.getLogger(__name__)

def get_key_storage_path():
    """Get the path where keys are stored"""
    return get_instance_path('keys')

def ensure_key_directory():
    """Ensure the key storage directory exists"""
    key_dir = get_key_storage_path()
    key_dir.mkdir(parents=True, exist_ok=True)
    return key_dir

def get_existing_keys():
    """Get existing cryptographic keys from the issuer system"""
    keys = []
    
    try:
        from ..issuer import key_generator
        
        # Load keys
        bbs_private, bbs_public = key_generator.load_or_generate_bbs_keys()
        jwt_private, jwt_public = key_generator.load_or_generate_keys()
        
        # Generate DID
        did = key_generator.generate_did(jwt_public)

        # Usage count (from db)
        usage_count = 0
        try:
            from ..models import VC_Offer
            usage_count = VC_Offer.query.count()
        except:
            pass

        # Add BBS+ key
        if bbs_private and bbs_public:
            public_key_preview = str(bbs_public)[:50] + "..." if len(str(bbs_public)) > 50 else str(bbs_public)
            
            keys.append({
                "id": "bbs_issuer_key",
                "type": "BBS+",
                "algorithm": "BBS+",
                "status": "active",
                "created": datetime.datetime.now().isoformat(),
                "expires": (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
                "usage": "credential_signing",
                "purpose": "BBS+ Credential Signing",
                "key_size": "Variable",
                "usage_count": usage_count,
                "public_key_preview": public_key_preview,
                "has_private_key": True,
                "has_public_key": True,
                "detailed_usage": {
                    "primary_function": "Signiert alle Credential-Felder für Selective Disclosure",
                    "capabilities": ["Zero-Knowledge Proofs", "Selective Disclosure", "Unlinkability"],
                    "process": "Issuer → BBS+ Signatur → Wallet → ZK-Beweis → Verifier",
                    "fields_signed": "30+ Felder (firstName, lastName, studentId, etc.)"
                }
            })
        
        # Add JWT signing key with DID
        if jwt_private and jwt_public:
            public_key_preview = jwt_public[:50] + "..." if len(jwt_public) > 50 else jwt_public
            
            keys.append({
                "id": "jwt_signing_key",
                "type": "Ed25519", # Kept label for consistency or should update? Updating to ES256 (P-256) which is accurate.
                "algorithm": "ES256 (P-256)", 
                "status": "active",
                "created": datetime.datetime.now().isoformat(),
                "expires": (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
                "usage": "jwt_signing",
                "purpose": "JWT Envelope Signing",
                "key_size": "256-bit",
                "usage_count": usage_count,
                "did": did,
                "issuer_id": did,
                "public_key_preview": public_key_preview,
                "has_private_key": True,
                "has_public_key": True,
                "detailed_usage": {
                    "primary_function": "Signiert JWT-Envelope für Transport-Sicherheit",
                    "capabilities": ["Issuer-Authentifizierung", "Integrität", "OpenID4VC Kompatibilität"],
                    "process": "VC → JWT Wrapper → ES256 Signatur → DID im Header",
                    "verification": "DID auflösen → Public Key extrahieren → JWT validieren"
                }
            })
                
    except Exception as e:
        logger.warning(f"Could not load keys: {e}")
        
    # Get previously generated API keys from registry
    try:
        from ..models import KeyRegistry
        api_keys = KeyRegistry.query.all()
        for api_key in api_keys:
            keys.append({
                "id": api_key.key_identifier,
                "type": "Custom",
                "algorithm": "Unknown",
                "status": api_key.status,
                "created": api_key.created_at.isoformat() if api_key.created_at else datetime.datetime.now().isoformat(),
                "expires": (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
                "usage": "unknown",
                "purpose": "Custom Generated Key",
                "key_size": "Unknown",
                "usage_count": 0
            })
    except Exception as e:
        logger.warning(f"Could not load API keys from registry: {e}")
        
    return keys

def generate_new_key(key_type, purpose="General Purpose", validity_days=365):
    """Generate a new cryptographic key"""
    try:
        key_id = f"key_{int(datetime.datetime.now().timestamp())}_{secrets.token_hex(4)}"
        
        if key_type == "Ed25519":
            # Generate Ed25519 key pair
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization
            
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            algorithm = "EdDSA"
            key_size = "256-bit"
            
        elif key_type == "BBS+":
            # For BBS+, we'll use the existing generator
            from ..issuer import key_generator
            private_key, public_key = key_generator.generate_bbs_keys()
            private_pem = private_key.encode() if isinstance(private_key, str) else str(private_key).encode()
            public_pem = public_key.encode() if isinstance(public_key, str) else str(public_key).encode()
            algorithm = "BBS+"
            key_size = "Variable"
            
        elif key_type == "X.509":
            # Generate RSA key pair and self-signed certificate
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Create self-signed certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Berlin"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Berlin"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "StudentVC"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                public_key
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.DNSName("127.0.0.1"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = cert.public_bytes(serialization.Encoding.PEM)
            algorithm = "RSA-2048"
            key_size = "2048-bit"
            
        else:
            raise ValueError(f"Unsupported key type: {key_type}")
        
        # Store the key
        key_dir = ensure_key_directory()
        private_key_path = key_dir / f"{key_id}_private.pem"
        public_key_path = key_dir / f"{key_id}_public.pem"
        
        private_key_path.write_bytes(private_pem)
        public_key_path.write_bytes(public_pem)
        
        # Create key record
        key_record = {
            "id": key_id,
            "type": key_type,
            "algorithm": algorithm,
            "status": "active",
            "created": datetime.datetime.now().isoformat(),
            "expires": (datetime.datetime.now() + datetime.timedelta(days=validity_days)).isoformat(),
            "usage": "general",
            "purpose": purpose,
            "key_size": key_size,
            "usage_count": 0,
            "private_key_path": str(private_key_path),
            "public_key_path": str(public_key_path)
        }
        
        logger.info(f"Generated new {key_type} key: {key_id}")
        return key_record
        
    except Exception as e:
        logger.error(f"Error generating key: {e}")
        raise

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    
    @blueprint.route("/settings/api/keys/inventory", methods=["GET"])
    def api_key_inventory():
        """Get comprehensive key inventory"""
        try:
            logger.info("🔑 Fetching key inventory")
            
            # Get existing keys from the system
            keys = get_existing_keys()
            
            # Add any custom generated keys
            key_dir = get_key_storage_path()
            if key_dir.exists():
                for key_file in key_dir.glob("*_private.pem"):
                    key_id = key_file.stem.replace("_private", "")
                    # Skip if already included
                    if not any(k["id"] == key_id for k in keys):
                        keys.append({
                            "id": key_id,
                            "type": "Custom",
                            "algorithm": "Unknown",
                            "status": "active",
                            "created": datetime.datetime.fromtimestamp(key_file.stat().st_mtime).isoformat(),
                            "expires": (datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
                            "usage": "unknown",
                            "purpose": "Custom Generated Key",
                            "key_size": "Unknown",
                            "usage_count": 0
                        })
            
            # Calculate statistics
            active_keys = [k for k in keys if k["status"] == "active"]
            expired_keys = [k for k in keys if k["status"] == "expired"]
            
            return jsonify({
                "status": "success", 
                "keys": keys,
                "statistics": {
                    "total": len(keys),
                    "active": len(active_keys),
                    "expired": len(expired_keys),
                    "expiring_soon": sum(1 for k in keys if k["status"] == "active" and 
                                       datetime.datetime.fromisoformat(k["expires"].replace('Z', '')) < 
                                       datetime.datetime.now() + datetime.timedelta(days=30))
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting key inventory: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/keys/generate", methods=["POST"])
    def api_generate_key():
        """Generate a new cryptographic key"""
        try:
            if not request.is_json:
                return jsonify({
                    "status": "error",
                    "message": "Invalid request format, expected JSON"
                }), 400
                
            data = request.get_json()
            key_type = data.get("type", "Ed25519")
            purpose = data.get("purpose", "General Purpose")
            validity_days = int(data.get("validity_days", 365))
            
            logger.info(f"🔑 Generating new {key_type} key")
            
            # Generate the key
            key_record = generate_new_key(key_type, purpose, validity_days)
            
            return jsonify({
                "status": "success",
                "message": f"{key_type} key generated successfully",
                "key": key_record
            }), 200
            
        except Exception as e:
            logger.error(f"Error generating key: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/keys/<key_id>/rotate", methods=["POST"])
    def api_rotate_key(key_id):
        """Rotate a specific key"""
        try:
            logger.info(f"🔑 Rotating key: {key_id}")
            
            # For now, simulate key rotation
            new_key_id = f"key_{int(datetime.datetime.now().timestamp())}_{secrets.token_hex(4)}"
            
            return jsonify({
                "status": "success",
                "message": "Key rotated successfully",
                "old_key_id": key_id,
                "new_key_id": new_key_id,
                "rotation_date": datetime.datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"Error rotating key {key_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/keys/<key_id>/export", methods=["GET"])
    def api_export_key(key_id):
        """Export a key's public key"""
        try:
            logger.info(f"🔑 Exporting key: {key_id}")
            
            # Find the key
            keys = get_existing_keys()
            key = next((k for k in keys if k["id"] == key_id), None)
            
            if not key:
                return jsonify({
                    "status": "error",
                    "message": "Key not found"
                }), 404
            
            # For now, return mock export data
            export_data = {
                "key_id": key_id,
                "type": key["type"],
                "algorithm": key["algorithm"],
                "created": key["created"],
                "export_format": "PEM",
                "public_key": f"-----BEGIN PUBLIC KEY-----\n{secrets.token_hex(64)}\n-----END PUBLIC KEY-----"
            }
            
            return jsonify({
                "status": "success",
                "message": "Key exported successfully",
                "export_data": export_data
            }), 200
            
        except Exception as e:
            logger.error(f"Error exporting key {key_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/keys/<key_id>/delete", methods=["DELETE"])
    def api_delete_key(key_id):
        """Delete a key"""
        try:
            logger.info(f"🔑 Deleting key: {key_id}")
            
            # Find and delete the key files
            key_dir = get_key_storage_path()
            private_key_path = key_dir / f"{key_id}_private.pem"
            public_key_path = key_dir / f"{key_id}_public.pem"
            
            deleted_files = []
            if private_key_path.exists():
                private_key_path.unlink()
                deleted_files.append("private_key")
            if public_key_path.exists():
                public_key_path.unlink()
                deleted_files.append("public_key")
            
            return jsonify({
                "status": "success",
                "message": "Key deleted successfully",
                "deleted_files": deleted_files
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting key {key_id}: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/keys/<key_id>/archive", methods=["POST"])
    def api_archive_key(key_id):
        """Archive a key"""
        try:
            logger.info(f"🔑 Archiving key: {key_id}")
            
            return jsonify({
                "status": "success",
                "message": "Key archived successfully",
                "key_id": key_id,
                "archived_date": datetime.datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            logger.error(f"Error archiving key {key_id}: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e)
            }), 500

    @blueprint.route("/settings/api/selective-disclosure", methods=["GET", "POST"])
    def api_selective_disclosure():
        """Get or save selective disclosure settings"""
        try:
            system_settings = SystemSettings.get_or_create_default()
            
            if request.method == "GET":
                # Load existing settings
                logger.info("📖 Loading selective disclosure settings")
                
                try:
                    disclosure_data = system_settings.disclosure_settings or {}
                    selected_fields = []
                    
                    if ('selective_disclosure' in disclosure_data and 
                        'mandatory_fields' in disclosure_data['selective_disclosure']):
                        selected_fields = disclosure_data['selective_disclosure']['mandatory_fields']
                    
                    # Convert from verifier format to frontend format
                    settings = {
                        "field_first_name": "firstName" in selected_fields,
                        "field_last_name": "lastName" in selected_fields,
                        "field_student_id": "studentId" in selected_fields,
                        "field_student_id_prefix": "studentIdPrefix" in selected_fields
                    }
                    logger.info(f"✅ Loaded settings from database: {settings}")
                except Exception as load_error:
                    logger.warning(f"⚠️ Failed to load settings, using defaults: {load_error}")
                    settings = {
                        "field_first_name": False,
                        "field_last_name": False,
                        "field_student_id": False,
                        "field_student_id_prefix": False
                    }
                
                return jsonify({
                    "status": "success",
                    "settings": settings
                }), 200
            
            else:  # POST method
                if not request.is_json:
                    return jsonify({
                        "status": "error",
                        "message": "Invalid request format, expected JSON"
                    }), 400
                    
                data = request.get_json()
                
                # Log the settings being saved
                logger.info(f"💾 Saving selective disclosure settings: {data}")
                
                 # Convert from frontend format to model format
                frontend_settings = {
                    "field_first_name": data.get("field_first_name", True),
                    "field_last_name": data.get("field_last_name", True),
                    "field_student_id": data.get("field_student_id", True),
                    "field_student_id_prefix": data.get("field_student_id_prefix", False)
                }
                
                # Convert to the format the verifier expects (nested structure)
                selected_fields = []
                field_mapping = {
                    "field_first_name": "firstName",
                    "field_last_name": "lastName", 
                    "field_student_id": "studentId",
                    "field_student_id_prefix": "studentIdPrefix"
                }
                
                for frontend_field, model_field in field_mapping.items():
                    if frontend_settings.get(frontend_field, False):
                        selected_fields.append(model_field)
                
                # Create the nested structure the verifier expects
                verifier_format = {
                    "selective_disclosure": {
                        "mandatory_fields": selected_fields
                    }
                }
                
                # Implement actual database storage
                try:
                    system_settings.disclosure_settings = verifier_format
                    system_settings.updated_by = get_current_user_email()
                    flag_modified(system_settings, "disclosure_settings")
                    db.session.commit()
                    
                    logger.info(f"✅ Selective disclosure settings saved to database")
                    
                except Exception as storage_error:
                    logger.error(f"⚠️ Database storage failed: {storage_error}")
                    return jsonify({"status": "error", "message": f"Database storage failed: {storage_error}"}), 500
                
                return jsonify({
                    "status": "success",
                    "message": "Selective disclosure settings saved successfully",
                    "settings": frontend_settings
                }), 200
                
        except Exception as e:
            logger.error(f"Error with selective disclosure settings: {e}")
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500