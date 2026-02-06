"""
Debug routes for testing selective disclosure
"""
from flask import Blueprint, jsonify
from .settings_integration import get_current_selective_disclosure_settings, get_presentation_definition
from logging import getLogger

logger = getLogger("LOGGER")

debug_bp = Blueprint('verifier_debug', __name__)


@debug_bp.route('/debug/selective-disclosure', methods=['GET'])
def debug_selective_disclosure():
    """
    Debug endpoint to show exactly what selective disclosure settings are being used
    """
    try:
        # Step 1: Get current settings
        current_fields = get_current_selective_disclosure_settings()
        
        # Step 2: Get presentation definition
        pres_def = get_presentation_definition()
        
        # Step 3: Count fields
        from .constants import TECHNICAL_FIELDS
        tech_count = len([f for f in current_fields if f in TECHNICAL_FIELDS])
        user_count = len(current_fields) - tech_count
        
        result = {
            "status": "success",
            "step_1_get_current_settings": {
                "total_fields": len(current_fields),
                "fields": current_fields,
                "technical_count": tech_count,
                "user_count": user_count
            },
            "step_2_presentation_definition": {
                "technical_fields": pres_def.get('technical_fields', []),
                "user_mandatory_fields": pres_def.get('user_mandatory_fields', []),
                "mandatory_fields": pres_def.get('mandatory_fields', []),
                "technical_count": len(pres_def.get('technical_fields', [])),
                "user_count": len(pres_def.get('user_mandatory_fields', []))
            },
            "diagnosis": {
                "database_to_settings_ok": user_count > 0,
                "settings_to_presentation_ok": len(pres_def.get('user_mandatory_fields', [])) > 0,
                "issue": None
            }
        }
        
        # Add diagnosis
        if user_count == 0:
            result["diagnosis"]["issue"] = "No user fields loaded from database. Check database settings."
        elif len(pres_def.get('user_mandatory_fields', [])) == 0:
            result["diagnosis"]["issue"] = "User fields loaded but not separated correctly in presentation definition."
        else:
            result["diagnosis"]["issue"] = None
            result["diagnosis"]["message"] = "Settings look correct! If wallet doesn't show fields, it's a wallet caching issue."
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        import traceback
        return jsonify({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

