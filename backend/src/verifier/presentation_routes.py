"""
Presentation Request Routes for the Verifier.

Handles QR code generation and presentation request creation.
"""

from flask import Blueprint, request, jsonify, redirect
from src.utils import get_current_server_url
from logging import getLogger
from urllib.parse import quote
import json
from ..models import VP_NONCE, VerificationSession, db
from .utils import randomString
from .settings_integration import get_presentation_definition
from .. import socketio

logger = getLogger("LOGGER")
presentation_bp = Blueprint("presentation", __name__)

aud_val = "did:key:tub-verifier-example"


@presentation_bp.route("/request_uri", methods=["GET", "POST"])
def request_uri():
    server_url = get_current_server_url() + "/verifier/"
    redirect_uri = f"openid4vp://?request_uri={server_url}presentation-request"
    return redirect(redirect_uri)


@presentation_bp.route("/request.uri/<request_uri_id>", methods=["GET", "POST"])
def request_uri_with_id(request_uri_id):
    """
    Handle specific request URI calls with IDs - supports both GET and POST for iOS wallet compatibility
    """
    try:
        # Try to find a specific session
        session = VerificationSession.query.get(request_uri_id)
        
        # Get global settings for defaults/fallback
        presentation_def = get_presentation_definition()
        
        mandatory_fields = []
        response_uri = get_current_server_url() + "/verifier/direct_post"
        nonce = randomString(10)

        if session:
            # Check status before proceeding
            if session.status == 'verified' or session.status == 'failed':
                 logger.warning(f"Attempt to reuse session {session.id} with status {session.status}")
                 return jsonify({"error": "This QR code has already been used or is invalid"}), 410  # 410 Gone

            # Session-based flow
            if session.status == 'created':
                session.status = 'scanned'
                db.session.commit()
            
            # Start with session requested fields
            mandatory_fields = list(session.requested_fields)
            
            # Add technical fields from global config
            field_mapping = presentation_def.get("field_mappings", {})
            for field in presentation_def.get("technical_fields", []):
                ios_field = field_mapping.get(field, field)
                if ios_field not in mandatory_fields:
                    mandatory_fields.append(ios_field)

            # Update response URI to include session ID
            response_uri = get_current_server_url() + f"/verifier/direct_post?session_id={session.id}"
            nonce = session.nonce
            
        else:
            # OLD/FALLBACK Logic
            # Create minimal field list with proper iOS mapping
            ios_compatible_fields = []
            field_mapping = presentation_def.get("field_mappings", {})

            # Add technical fields with iOS camelCase mapping
            for field in presentation_def.get("technical_fields", []):
                ios_field = field_mapping.get(field, field)
                if ios_field not in ios_compatible_fields:
                    ios_compatible_fields.append(ios_field)

            # Add user mandatory fields, skip complex fields
            complex_fields = [
                "image",
                "theme",
                "vc.credentialSubject.image",
                "vc.credentialSubject.theme",
            ]
            for field in presentation_def.get("user_mandatory_fields", []):
                if field not in complex_fields and field not in ios_compatible_fields:
                    ios_compatible_fields.append(field)
            
            mandatory_fields = ios_compatible_fields

        # MINIMAL response parameters
        params = {
            "response_type": "vp_token",
            "response_uri": response_uri,
            "response_mode": "direct_post",
            "presentation_definition": json.dumps(
                {
                    "mandatory_fields": mandatory_fields,
                    "explanation": {}
                }, 
                separators=(",", ":")
            ),
            "state": nonce,
            "nonce": nonce
        }

        if request.method == "GET":
            response = jsonify(params)
            # Disable caching to ensure subsequent scans (re-use attempts) hit the server logic
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response, 200
        else:  # POST
            # For iOS wallet compatibility - return 302 redirect with openid4vp scheme
            openid_url = f"openid4vp://?response_uri={params['response_uri']}&presentation_definition={params['presentation_definition']}&nonce={nonce}&state={nonce}"
            return redirect(openid_url, code=302)

    except Exception as e:
        logger.error(f"Error in request.uri endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@presentation_bp.route("/presentation-request", methods=["POST", "GET"])
def create_presentation_request():
    try:
        params = {}
        params["response_type"] = "vp_token"
        params["response_uri"] = get_current_server_url() + "/verifier/direct_post"
        params["response_mode"] = "direct_post"
        params["state"] = randomString(10)
        global nonce_val
        nonce_val = randomString(10)
        params["nonce"] = nonce_val

        params["aud"] = aud_val
        # Get structured presentation definition with field categories
        store_nonce(nonce_val)

        presentation_def = get_presentation_definition()

        # ✅ ENHANCED DEBUG: Log what we got from get_presentation_definition
        logger.info("=" * 80)
        logger.info("🔍 SELECTIVE DISCLOSURE DEBUG - PRESENTATION DEFINITION")
        logger.info("=" * 80)
        logger.info(
            f"📋 Technical fields (always required): {presentation_def.get('technical_fields', [])}"
        )
        logger.info(
            f"👤 User mandatory fields (selected by admin): {presentation_def.get('user_mandatory_fields', [])}"
        )
        logger.info(
            f"📊 ALL mandatory fields (combined): {presentation_def.get('mandatory_fields', [])}"
        )
        logger.info(
            f"🗂️  Field mappings available: {list(presentation_def.get('field_mappings', {}).keys())}"
        )
        logger.info("=" * 80)

        # Create minimal iOS-compatible field list
        ios_compatible_fields = []
        field_mapping = presentation_def.get("field_mappings", {})

        # Only add technical fields (always required, minimal set)
        for field in presentation_def["technical_fields"]:
            ios_field = field_mapping.get(field, field)
            if ios_field not in ios_compatible_fields:
                ios_compatible_fields.append(ios_field)

        # ✅ Add user mandatory fields, but skip complex fields and map nested fields to iOS format
        complex_fields = [
            "image",
            "theme",
            "vc.credentialSubject.image",
            "vc.credentialSubject.theme",
        ]
        logger.info(
            f"🔍 Processing {len(presentation_def['user_mandatory_fields'])} user mandatory fields..."
        )

        for field in presentation_def["user_mandatory_fields"]:
            logger.info(f"  ➤ Processing user field: '{field}'")

            if field in complex_fields:
                logger.info(f"    ⚠️  Skipping complex field: '{field}'")
                continue

            # Map nested field names to iOS-compatible format
            if field.startswith("vc.credentialSubject."):
                ios_field = field.replace("vc.credentialSubject.", "")
                logger.info(f"    🔄 Converted path '{field}' → '{ios_field}'")

                # Fix case sensitivity issues for iOS wallet compatibility
                ios_field_mapping = {
                    "studentId": "studentID",  # iOS uses uppercase ID
                    "studentIdPrefix": "studentIDPrefix",  # iOS uses uppercase ID
                }

                # Use the iOS-compatible field name if available
                original_ios_field = ios_field
                ios_field = ios_field_mapping.get(ios_field, ios_field)
                if ios_field != original_ios_field:
                    logger.info(
                        f"    🔄 Mapped case '{original_ios_field}' → '{ios_field}' for iOS"
                    )

                if ios_field not in ios_compatible_fields:
                    ios_compatible_fields.append(ios_field)
                    logger.info(f"    ✅ Added field: '{ios_field}'")
                else:
                    logger.info(f"    ⏭️  Field '{ios_field}' already in list")
            elif field not in ios_compatible_fields:
                ios_compatible_fields.append(field)
                logger.info(f"    ✅ Added field: '{field}'")
            else:
                logger.info(f"    ⏭️  Field '{field}' already in list")

        logger.info(
            f"✅ Total iOS-compatible fields after adding user fields: {len(ios_compatible_fields)}"
        )
        logger.info(f"📋 Final iOS-compatible fields list: {ios_compatible_fields}")

        # Create explanations for the fields (iOS app requires this)
        presentation_explanation = {
            "totalMessages": "Amount of messages in the whole credential. Needed for BBS+ signature verification",
            "bbsDPK": "BBS+ issuer public key, needed to check if credential was signed by a trusted issuer",
            "iss": "Issuer DID, needed to check if credential was signed by a trusted issuer",
            "sub": "Holder DID, needed to check if credential was signed by a trusted holder",
            "exp": "Expiration timestamp of the credential",
            "nbf": "Not before timestamp, when the credential becomes valid",
            "jti": "JWT ID, unique identifier for this credential",
            "nonce": "Prevents replay attacks, used to verify issuer signature",
            "signedNonce": "Signature of the nonce, used to verify issuer signature",
            "validityIdentifier": "Unique identifier of the credential, needed to check if credential is valid",
            # User field explanations
            "firstName": "First name of the cardholder",
            "lastName": "Last name of the cardholder",
            "studentID": "Unique student identification number",  # iOS uses uppercase ID
            "studentIDPrefix": "Prefix of the student ID for organization identification",  # iOS uses uppercase ID
        }

        # ✅ FINAL VERIFICATION: Log the complete field list before sending to wallet
        logger.info("=" * 80)
        logger.info("📤 FINAL PRESENTATION REQUEST TO WALLET")
        logger.info("=" * 80)
        logger.info(f"📋 Total mandatory fields: {len(ios_compatible_fields)}")
        logger.info(f"📋 Field list: {ios_compatible_fields}")

        # Count technical vs user fields
        from .constants import TECHNICAL_FIELDS

        tech_count = sum(
            1
            for f in ios_compatible_fields
            if f in TECHNICAL_FIELDS
            or f
            in [
                "iss",
                "sub",
                "exp",
                "nbf",
                "jti",
                "nonce",
                "signedNonce",
                "bbsDPK",
                "totalMessages",
                "validityIdentifier",
            ]
        )
        user_count = len(ios_compatible_fields) - tech_count
        logger.info(f"📊 Technical fields: {tech_count}, User fields: {user_count}")
        logger.info("=" * 80)

        # iOS app expects BOTH mandatory_fields AND explanation
        presentation_def_with_explanation = {
            "mandatory_fields": ios_compatible_fields,
            "explanation": {
                field: presentation_explanation.get(field, "No explanation available")
                for field in ios_compatible_fields
            },
        }

        # Compact JSON encoding
        presentation_def_json = json.dumps(
            presentation_def_with_explanation, separators=(",", ":")
        )
        logger.info(f"📦 JSON payload length: {len(presentation_def_json)} characters")
        params["presentation_definition"] = presentation_def_json

        # Construct the complete URL for the wallet
        client_id = get_current_server_url() + "/verifier/authorize"
        openid_request = f"openid4vp://?client_id={client_id}"
        for key, value in params.items():
            encoded_value = quote(str(value), safe="")
            openid_request += f"&{key}={encoded_value}"

        logger.info(
            f"Generated minimal presentation URL length: {len(openid_request)} chars"
        )

        # Emit success event like working version
        socketio.emit(
            "presentation_requested",
            {
                "status": "success",
                "message": "Presentation request created successfully.",
            },
        )

        # iOS wallet expects a redirect, not JSON!
        return redirect(openid_request)

    except Exception as e:
        logger.error(f"Error creating presentation request: {str(e)}")
        socketio.emit("presentation_requested", {"status": "error", "message": str(e)})
        return jsonify({"error": "something went wrong when requesting params"}), 500


def store_nonce(nonce):
    
    
    vp_nonce = VP_NONCE()
    vp_nonce.nonce = nonce

    db.session.add(vp_nonce)
    db.session.commit()


def get_aud_val():
    return aud_val
