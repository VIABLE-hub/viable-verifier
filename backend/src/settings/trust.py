from flask import request, jsonify, render_template
import logging
import json
import re
import time
from datetime import datetime

from .. import db
from ..models import SystemSettings
from .core import create_settings_backup

# Initialize logger for trust module
logger = logging.getLogger(__name__)

# Emergency fallback data
EMERGENCY_TRUST_DATA = {
    "trust": {
        "trusted_issuers": [
            {"id": "did:web:example.edu", "name": "Example University", "status": "active", "added": "2021-01-15T08:00:00Z"}
        ],
        "trusted_schemas": [
            {"id": "https://schema.org/EducationalCredential", "name": "Educational Credential", "status": "active", "added": "2021-01-15T08:00:00Z"}
        ],
        "verification_policies": {
            "require_proof": True,
            "check_revocation": True,
            "check_expiry": True,
            "allow_self_issued": False
        },
        "trust_registry": {
            "use_external": False,
            "endpoint": "",
            "api_key": "",
            "cache_minutes": 60
        }
    }
}

def validate_trust_settings(data):
    """
    Validate trust settings data
    """
    try:
        # Validate structure
        if not isinstance(data, dict):
            return False, "Invalid data format"
        
        # Validate trust section
        if "trust" not in data:
            return False, "Missing trust section"
        
        trust = data["trust"]
        if not isinstance(trust, dict):
            return False, "Invalid trust format"
        
        # Validate trusted_issuers
        if "trusted_issuers" not in trust:
            return False, "Missing trusted_issuers in trust settings"
        
        if not isinstance(trust["trusted_issuers"], list):
            return False, "trusted_issuers must be a list"
        
        # Validate trusted_schemas
        if "trusted_schemas" not in trust:
            return False, "Missing trusted_schemas in trust settings"
        
        if not isinstance(trust["trusted_schemas"], list):
            return False, "trusted_schemas must be a list"
        
        # Validate verification policies
        if "verification_policies" not in trust:
            return False, "Missing verification_policies in trust settings"
        
        verification_policies = trust["verification_policies"]
        if not isinstance(verification_policies, dict):
            return False, "verification_policies must be an object"
        
        # Validate trust registry
        if "trust_registry" not in trust:
            return False, "Missing trust_registry in trust settings"
        
        trust_registry = trust["trust_registry"]
        if not isinstance(trust_registry, dict):
            return False, "trust_registry must be an object"
        
        # Check required fields
        required_registry_fields = ["use_external", "endpoint", "api_key", "cache_minutes"]
        for field in required_registry_fields:
            if field not in trust_registry:
                return False, f"trust_registry must include {field}"
            
        # Check types
        if not isinstance(trust_registry["use_external"], bool):
            return False, "trust_registry.use_external must be a boolean"
        
        if not isinstance(trust_registry["endpoint"], str):
            return False, "trust_registry.endpoint must be a string"
        
        if not isinstance(trust_registry["api_key"], str):
            return False, "trust_registry.api_key must be a string"
        
        if not isinstance(trust_registry["cache_minutes"], (int, float)):
            return False, "trust_registry.cache_minutes must be a number"
        
        # If use_external is true, endpoint must be a valid URL
        if trust_registry["use_external"] and not trust_registry["endpoint"]:
            return False, "When use_external is true, endpoint must be provided"
        
        # Validate endpoint URL if provided
        if trust_registry["endpoint"]:
            url_pattern = re.compile(r'^https?://[\w.-]+(:\d+)?(/[\w./\-]*)?$')
            if not url_pattern.match(trust_registry["endpoint"]):
                return False, "trust_registry.endpoint must be a valid URL"
        
        # All validations passed
        return True, "Valid"
    except Exception as e:
        logger.error(f"Error validating trust settings: {e}")
        return False, str(e)

def api_trust_settings():
    """API endpoint for trust settings"""
    system_settings = SystemSettings.get_or_create_default()
    
    if request.method == "GET":
        # Return current settings
        trust_settings = system_settings.trust_settings or {
            "trust": {
                "trusted_issuers": [],
                "trusted_schemas": [],
                "trust_registry_url": None,
                "auto_update": False
            }
        }
        return jsonify({"status": "success", "data": trust_settings})
    
    elif request.method == "POST":
        try:
            data = request.json
            
            # Validate the settings
            valid, message = validate_trust_settings(data)
            if not valid:
                return jsonify({"status": "error", "message": message}), 400
            
            # Create backup
            create_settings_backup("auto", "Before trust settings update")
            
            # Update settings
            system_settings.trust_settings = data
            db.session.commit()
            
            return jsonify({"status": "success", "message": "Trust settings updated"})
        except Exception as e:
            logger.error(f"Error updating trust settings: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

def register_routes(blueprint):
    """Register routes with the provided blueprint"""
    
    # Define routes
    @blueprint.route("/settings/trust", methods=["GET"])
    def settings_trust_get():
        """Render the trust settings page"""
        return render_template("settings/trust.html")
    
    @blueprint.route("/settings/trust", methods=["POST"])
    def settings_trust_post():
        """Update trust settings"""
        return api_trust_settings()
    
    @blueprint.route("/settings/trust/issuer", methods=["POST"])
    def settings_trust_add_issuer():
        """Add a trusted issuer"""
        system_settings = SystemSettings.get_or_create_default()
        
        try:
            data = request.json
            issuer = data.get("issuer")
            
            if not issuer:
                return jsonify({"status": "error", "message": "Issuer is required"}), 400
            
            # Get current settings
            trust_settings = system_settings.trust_settings or {
                "trust": {
                    "trusted_issuers": [],
                    "trusted_schemas": [],
                    "trust_registry_url": None,
                    "auto_update": False
                }
            }
            
            # Add issuer if not already in the list
            if issuer not in trust_settings["trust"]["trusted_issuers"]:
                trust_settings["trust"]["trusted_issuers"].append(issuer)
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success", 
                    "message": "Trusted issuer added",
                    "data": trust_settings["trust"]["trusted_issuers"]
                })
            else:
                return jsonify({
                    "status": "warning", 
                    "message": "Issuer already trusted",
                    "data": trust_settings["trust"]["trusted_issuers"]
                })
        except Exception as e:
            logger.error(f"Error adding trusted issuer: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500
    
    @blueprint.route("/settings/trust/issuer/remove", methods=["POST"])
    def settings_trust_remove_issuer():
        """Remove a trusted issuer"""
        system_settings = SystemSettings.get_or_create_default()
        
        try:
            data = request.json
            issuer = data.get("issuer")
            
            if not issuer:
                return jsonify({"status": "error", "message": "Issuer is required"}), 400
            
            # Get current settings
            trust_settings = system_settings.trust_settings or {
                "trust": {
                    "trusted_issuers": [],
                    "trusted_schemas": [],
                    "trust_registry_url": None,
                    "auto_update": False
                }
            }
            
            # Remove issuer if in the list
            if issuer in trust_settings["trust"]["trusted_issuers"]:
                trust_settings["trust"]["trusted_issuers"].remove(issuer)
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success", 
                    "message": "Trusted issuer removed",
                    "data": trust_settings["trust"]["trusted_issuers"]
                })
            else:
                return jsonify({
                    "status": "warning", 
                    "message": "Issuer not in trusted list",
                    "data": trust_settings["trust"]["trusted_issuers"]
                })
        except Exception as e:
            logger.error(f"Error removing trusted issuer: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

    @blueprint.route("/settings/api/trust/issuers", methods=["GET", "POST", "DELETE"])
    def api_trust_issuers():
        """
        Handle trusted issuers API endpoint
        """
        try:
            system_settings = SystemSettings.get_or_create_default()
            
            # Get current trust settings or use defaults
            trust_settings = system_settings.trust_settings or {"trust": {"trusted_issuers": []}}
            if "trust" not in trust_settings:
                trust_settings["trust"] = {"trusted_issuers": []}
            if "trusted_issuers" not in trust_settings["trust"]:
                trust_settings["trust"]["trusted_issuers"] = []
            
            if request.method == "GET":
                # Return list of trusted issuers
                return jsonify({
                    "status": "success",
                    "issuers": trust_settings["trust"]["trusted_issuers"]
                }), 200
                
            elif request.method == "POST":
                # Add a new trusted issuer
                if not request.is_json:
                    return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                    
                data = request.get_json()
                issuer_id = data.get("id")
                issuer_name = data.get("name", issuer_id)
                
                if not issuer_id:
                    return jsonify({"status": "error", "message": "Missing issuer ID"}), 400
                
                # Check if issuer already exists
                for issuer in trust_settings["trust"]["trusted_issuers"]:
                    if isinstance(issuer, dict) and issuer.get("id") == issuer_id:
                        return jsonify({"status": "error", "message": "Issuer already exists"}), 400
                
                # Add new issuer
                new_issuer = {
                    "id": issuer_id,
                    "name": issuer_name,
                    "status": "active",
                    "added": datetime.now().isoformat()
                }
                
                trust_settings["trust"]["trusted_issuers"].append(new_issuer)
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Trusted issuer added",
                    "issuer": new_issuer
                }), 201
                
            elif request.method == "DELETE":
                # Remove a trusted issuer
                if not request.is_json:
                    return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                    
                data = request.get_json()
                issuer_id = data.get("id")
                
                if not issuer_id:
                    return jsonify({"status": "error", "message": "Missing issuer ID"}), 400
                
                # Find and remove issuer
                found = False
                for i, issuer in enumerate(trust_settings["trust"]["trusted_issuers"]):
                    if isinstance(issuer, dict) and issuer.get("id") == issuer_id:
                        del trust_settings["trust"]["trusted_issuers"][i]
                        found = True
                        break
                
                if not found:
                    return jsonify({"status": "error", "message": "Issuer not found"}), 404
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Trusted issuer removed"
                }), 200
        except Exception as e:
            logger.error(f"Error handling trusted issuers: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

    @blueprint.route("/settings/api/trust/schemas", methods=["GET", "POST", "DELETE"])
    def api_trust_schemas():
        """
        Handle trusted schemas API endpoint
        """
        try:
            system_settings = SystemSettings.get_or_create_default()
            
            # Get current trust settings or use defaults
            trust_settings = system_settings.trust_settings or {"trust": {"trusted_schemas": []}}
            if "trust" not in trust_settings:
                trust_settings["trust"] = {"trusted_schemas": []}
            if "trusted_schemas" not in trust_settings["trust"]:
                trust_settings["trust"]["trusted_schemas"] = []
            
            if request.method == "GET":
                # Return list of trusted schemas
                return jsonify({
                    "status": "success",
                    "schemas": trust_settings["trust"]["trusted_schemas"]
                }), 200
                
            elif request.method == "POST":
                # Add a new trusted schema
                if not request.is_json:
                    return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                    
                data = request.get_json()
                schema_id = data.get("id")
                schema_name = data.get("name", schema_id)
                
                if not schema_id:
                    return jsonify({"status": "error", "message": "Missing schema ID"}), 400
                
                # Check if schema already exists
                for schema in trust_settings["trust"]["trusted_schemas"]:
                    if isinstance(schema, dict) and schema.get("id") == schema_id:
                        return jsonify({"status": "error", "message": "Schema already exists"}), 400
                
                # Add new schema
                new_schema = {
                    "id": schema_id,
                    "name": schema_name,
                    "status": "active",
                    "added": datetime.now().isoformat()
                }
                
                trust_settings["trust"]["trusted_schemas"].append(new_schema)
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Trusted schema added",
                    "schema": new_schema
                }), 201
                
            elif request.method == "DELETE":
                # Remove a trusted schema
                if not request.is_json:
                    return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                    
                data = request.get_json()
                schema_id = data.get("id")
                
                if not schema_id:
                    return jsonify({"status": "error", "message": "Missing schema ID"}), 400
                
                # Find and remove schema
                found = False
                for i, schema in enumerate(trust_settings["trust"]["trusted_schemas"]):
                    if isinstance(schema, dict) and schema.get("id") == schema_id:
                        del trust_settings["trust"]["trusted_schemas"][i]
                        found = True
                        break
                
                if not found:
                    return jsonify({"status": "error", "message": "Schema not found"}), 404
                
                # Update settings
                system_settings.trust_settings = trust_settings
                db.session.commit()
                
                return jsonify({
                    "status": "success",
                    "message": "Trusted schema removed"
                }), 200
        except Exception as e:
            logger.error(f"Error handling trusted schemas: {e}")
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 500

    @blueprint.route("/settings/api/trust/verify", methods=["POST"])
    def api_trust_verify():
        """
        Verify if an issuer or schema is trusted
        """
        try:
            if not request.is_json:
                return jsonify({"status": "error", "message": "Invalid request format, expected JSON"}), 400
                
            data = request.get_json()
            issuer_id = data.get("issuer_id")
            schema_id = data.get("schema_id")
            
            if not issuer_id and not schema_id:
                return jsonify({"status": "error", "message": "Either issuer_id or schema_id is required"}), 400
            
            system_settings = SystemSettings.get_or_create_default()
            
            # Get current trust settings or use defaults
            trust_settings = system_settings.trust_settings or EMERGENCY_TRUST_DATA
            
            # Access the nested structure safely
            trust_data = trust_settings.get("trust", {}) if "trust" in trust_settings else trust_settings
            
            result = {
                "issuer_trusted": False,
                "schema_trusted": False
            }
            
            # Check issuer if provided
            if issuer_id:
                for issuer in trust_data.get("trusted_issuers", []):
                    if isinstance(issuer, dict) and issuer.get("id") == issuer_id and issuer.get("status") == "active":
                        result["issuer_trusted"] = True
                        break
            
            # Check schema if provided
            if schema_id:
                for schema in trust_data.get("trusted_schemas", []):
                    if isinstance(schema, dict) and schema.get("id") == schema_id and schema.get("status") == "active":
                        result["schema_trusted"] = True
                        break
            
            return jsonify({
                "status": "success",
                "result": result
            }), 200
        except Exception as e:
            logger.error(f"Error verifying trust: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
