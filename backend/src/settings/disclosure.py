from flask import request, jsonify, render_template
import logging
import json
from .. import db
from ..models import SystemSettings
from .core import create_settings_backup

logger = logging.getLogger(__name__)

# Global variable to hold the blueprint reference
settings = None

def validate_disclosure_settings(data):
    """Validate selective disclosure settings"""
    try:
        # Validate structure
        if not isinstance(data, dict):
            return False, "Invalid data format"
        
        # Validate selective_disclosure section
        if "selective_disclosure" not in data:
            return False, "Missing selective_disclosure section"
        
        sd = data["selective_disclosure"]
        if not isinstance(sd, dict):
            return False, "Invalid selective_disclosure format"
        
        # Validate mandatory_fields
        if "mandatory_fields" not in sd:
            return False, "Missing mandatory_fields in selective_disclosure"
        
        if not isinstance(sd["mandatory_fields"], list):
            return False, "mandatory_fields must be a list"
        
        # All validations passed
        return True, "Valid"
    except Exception as e:
        logger.error(f"Error validating disclosure settings: {e}")
        return False, str(e)

def api_disclosure_settings():
    """API endpoint for selective disclosure settings"""
    system_settings = SystemSettings.get_or_create_default()
    
    if request.method == "GET":
        # Return current settings
        disclosure_settings = system_settings.disclosure_settings or {"selective_disclosure": {"mandatory_fields": []}}
        return jsonify({"status": "success", "data": disclosure_settings})
    
    elif request.method == "POST":
        try:
            data = request.json
            
            # Validate the settings
            valid, message = validate_disclosure_settings(data)
            if not valid:
                return jsonify({"status": "error", "message": message}), 400
            
            # Create backup
            create_settings_backup("auto", "Before disclosure settings update")
            
            # Update settings
            system_settings.disclosure_settings = data
            db.session.commit()
            
            # Update verifier
            from .core import initialize_verifier_from_database
            initialize_verifier_from_database()
            
            return jsonify({"status": "success", "message": "Disclosure settings updated"})
        except Exception as e:
            logger.error(f"Error updating disclosure settings: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    
    # Define routes
    @blueprint.route("/settings/selective-disclosure", methods=["GET"])
    def disclosure_selective_disclosure_get():
        """Get current selective disclosure settings"""
        system_settings = SystemSettings.get_or_create_default()
        
        try:
            # Get current settings - return only user-selected fields, not technical fields
            disclosure_settings = system_settings.disclosure_settings or {}
            selective_disclosure = disclosure_settings.get("selective_disclosure", {})
            stored_fields = selective_disclosure.get("mandatory_fields", [])
            
            # Filter to only return user fields (no technical fields) and convert to simple names
            user_fields = []
            for field in stored_fields:
                # Skip technical fields
                if field in ['total_messages', 'bbs_dpk', 'iss', 'sub', 'exp', 'nbf', 'jti', 'nonce', 'signed_nonce', 'validity_identifier']:
                    continue
                
                # Convert full paths to simple names for frontend compatibility
                if field.startswith('vc.credentialSubject.'):
                    simple_name = field.replace('vc.credentialSubject.', '')
                    user_fields.append(simple_name)
                else:
                    # Field is already a simple name
                    user_fields.append(field)
            
            logger.debug(f"GET selective disclosure - stored: {stored_fields}, returning user fields: {user_fields}")
            
            return jsonify({
                "status": "success",
                "mandatory_fields": user_fields
            })
        except Exception as e:
            logger.error(f"Error getting selective disclosure settings: {e}")
            return jsonify({
                "status": "error", 
                "message": str(e),
                "mandatory_fields": []
            }), 500
    
    @blueprint.route("/settings/selective-disclosure", methods=["POST"])
    def disclosure_selective_disclosure_post():
        """Update selective disclosure settings"""
        try:
            logger.info(f"POST selective disclosure")
            
            system_settings = SystemSettings.get_or_create_default()
            logger.info(f"POST selective disclosure - system_settings created/retrieved: {system_settings}")
            
            data = request.json
            logger.info(f"POST selective disclosure - received data: {data}")
            
            # Map frontend field names to credential field names
            def map_frontend_to_credential_field(frontend_field):
                mapping = {
                    "firstName": "firstName",
                    "lastName": "lastName",
                    "studentId": "studentId",
                    "studentIdPrefix": "studentIdPrefix",
                    "image": "image",
                    "theme": "theme",
                    "email": "email",
                    "phoneNumber": "phoneNumber",
                    "dateOfBirth": "dateOfBirth",
                    "address": "address",
                    "city": "city",
                    "postalCode": "postalCode",
                    "country": "country",
                    "idNumber": "idNumber",
                    "nationality": "nationality",
                    "gender": "gender",
                    "issuanceDate": "issuanceDate",
                    "expiryDate": "expiryDate"
                }
                return mapping.get(frontend_field, frontend_field)
            
            # Process the selected fields - store as simple names for consistency
            mandatory_fields = []
            # Accept both "selectedFields" and "mandatory_fields" for compatibility
            selected_fields = data.get("mandatory_fields", data.get("selectedFields", []))
            
            # Validate fields against allowed list
            allowed_fields = ['firstName', 'lastName', 'studentId', 'studentIdPrefix', 'image', 'theme']
            
            for field in selected_fields:
                credential_field = map_frontend_to_credential_field(field)
                # Only store user fields that are in the allowed list
                if credential_field in allowed_fields:
                    mandatory_fields.append(credential_field)
                else:
                    logger.warning(f"Ignoring unknown field: {field}")
            
            logger.info(f"POST selective disclosure - received: {selected_fields}, storing: {mandatory_fields}")
            
            # Create or update the disclosure settings
            disclosure_settings = system_settings.disclosure_settings or {}
            if "selective_disclosure" not in disclosure_settings:
                disclosure_settings["selective_disclosure"] = {}
            
            disclosure_settings["selective_disclosure"]["mandatory_fields"] = mandatory_fields
            
            # Save the settings - CRITICAL: Use flag_modified for JSON columns
            system_settings.disclosure_settings = disclosure_settings
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(system_settings, 'disclosure_settings')
            logger.info(f"POST selective disclosure - updated disclosure_settings: {disclosure_settings}")
            
            # Commit to database
            try:
                db.session.commit()
                logger.info("POST selective disclosure - database commit successful")
            except Exception as commit_error:
                logger.error(f"POST selective disclosure - database commit failed: {commit_error}")
                db.session.rollback()
                raise commit_error
            
            # Update verifier
            from .core import initialize_verifier_from_database
            initialize_verifier_from_database()
            
            return jsonify({"success": True, "status": "success", "message": "Selective disclosure settings updated"})
        except Exception as e:
            logger.error(f"Error updating selective disclosure settings: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @blueprint.route("/settings/api/credential-fields", methods=["GET"])
    def disclosure_api_credential_fields():
        """Get available credential fields"""
        try:
            # Get schema from verifier module
            from src.verifier import verifier as verifier_module
            schema = verifier_module.credential_schema
            
            # Extract fields from schema
            def extract_fields_from_dict(data_dict, prefix=''):
                fields = []
                if not isinstance(data_dict, dict):
                    return fields
                
                for key, value in data_dict.items():
                    if key == "type" or key == "@context":
                        continue
                    
                    field_path = f"{prefix}{key}" if prefix else key
                    
                    if isinstance(value, dict):
                        # Recursive call for nested objects
                        nested_fields = extract_fields_from_dict(value, f"{field_path}.")
                        fields.extend(nested_fields)
                    else:
                        # Add leaf field
                        fields.append({
                            "id": field_path,
                            "name": key,
                            "path": field_path,
                            "type": "string"  # Default type
                        })
                
                return fields
            
            # Get credential subject fields
            credential_subject = schema.get("credentialSubject", {})
            fields = extract_fields_from_dict(credential_subject)
            
            # Map fields to frontend format
            def map_credential_to_frontend_field(credential_field):
                mapping = {
                    "firstName": {"id": "firstName", "name": "First Name", "type": "string"},
                    "lastName": {"id": "lastName", "name": "Last Name", "type": "string"},
                    "email": {"id": "email", "name": "Email", "type": "string"},
                    "phoneNumber": {"id": "phoneNumber", "name": "Phone Number", "type": "string"},
                    "dateOfBirth": {"id": "dateOfBirth", "name": "Date of Birth", "type": "date"},
                    "address": {"id": "address", "name": "Address", "type": "string"},
                    "city": {"id": "city", "name": "City", "type": "string"},
                    "postalCode": {"id": "postalCode", "name": "Postal Code", "type": "string"},
                    "country": {"id": "country", "name": "Country", "type": "string"},
                    "idNumber": {"id": "idNumber", "name": "ID Number", "type": "string"},
                    "nationality": {"id": "nationality", "name": "Nationality", "type": "string"},
                    "gender": {"id": "gender", "name": "Gender", "type": "string"},
                    "issuanceDate": {"id": "issuanceDate", "name": "Issuance Date", "type": "date"},
                    "expiryDate": {"id": "expiryDate", "name": "Expiry Date", "type": "date"}
                }
                
                field_id = credential_field.get("id")
                if field_id in mapping:
                    return mapping[field_id]
                return credential_field
            
            # Map fields
            mapped_fields = [map_credential_to_frontend_field(field) for field in fields]
            
            return jsonify({"status": "success", "data": mapped_fields})
        except Exception as e:
            logger.error(f"Error getting credential fields: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @blueprint.route("/settings/selective-disclosure/debug", methods=["GET"])
    def disclosure_debug_selective_disclosure():
        """Debug endpoint for selective disclosure settings"""
        
        system_settings = SystemSettings.get_or_create_default()
        
        try:
            # Get current settings
            disclosure_settings = system_settings.disclosure_settings or {}
            
            # Get verifier settings
            from src.verifier import verifier as verifier_module
            verifier_settings = verifier_module.presentation_definition.get("mandatory_fields", [])
            
            return jsonify({
                "status": "success",
                "data": {
                    "database_settings": disclosure_settings,
                    "verifier_settings": verifier_settings
                }
            })
        except Exception as e:
            logger.error(f"Error debugging selective disclosure: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
