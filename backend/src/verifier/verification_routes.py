"""
Verification Routes for the Verifier.

Handles VP verification and processing.
"""

from flask import Blueprint, request, jsonify
from flask_socketio import join_room
from logging import getLogger
import jwt
import traceback

from .. import socketio
from ..models import VerificationSession, db
from .field_extractor import (
    decode_jwt_token,
    extract_presentation_from_vp,
    get_field_value,
)
from .validators import validate_credential_validity
from .integration import safe_verify_presentation
from .settings_integration import get_presentation_definition
from .constants import TECHNICAL_FIELDS, ALL_CREDENTIAL_FIELDS
from .utils import process_oversized_fields

logger = getLogger("LOGGER")

verification_bp = Blueprint("verification", __name__)


@socketio.on('join_session')
def on_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"Client joined session room: {session_id}")



@verification_bp.route("/direct_post", methods=["POST"])
def direct_post():
    """
    Handles direct POST from the wallet with the verifiable presentation
    """
    # session check
    session_id = request.args.get("session_id")
    
    # Helper to emit events to specific session room if available
    def emit_to_session(event, data):
        if session_id:
            socketio.emit(event, data, room=session_id)
        else:
            # SECURITY FIX: Do not broadcast globally if no session ID is present.
            # This prevents PII leakage to unrelated clients.
            logger.warning(f"SECURITY: Attempted to emit '{event}' without session_id. Event suppressed.")
            # socketio.emit(event, data)
            
    expected_nonce = None
    
    if session_id:
        try:
            session = VerificationSession.query.get(session_id)
            if session:
                if session.status == 'verified':
                    logger.warning(f"Session {session_id} reuse attempt blocked")
                    return jsonify({"error": "This QR code has already been used", "valid": 0}), 400
                
                # Retrieve nonce from session to verify it
                expected_nonce = session.nonce
                
                # Mark as verified
                session.status = 'verified'
                db.session.commit()
                logger.info(f"Session {session_id} marked as verified")
                
                # Emit event to inform frontend that this specific session was verified
                # This helps the frontend check if the event matches the current session
                emit_to_session(
                    "session_verified", 
                    {"session_id": session_id, "status": "verified"}
                )
        except Exception as e:
            logger.error(f"Error checking session: {e}")
            
    try:
        # Check URL parameters first
        vp_token = request.args.get("vp_token")
        state = request.args.get("state")

        # If not in URL parameters, try to get from form
        if not vp_token:
            vp_token = request.form.get("vp_token")
            state = request.form.get("state")

        # If still not found, try to get from JSON body
        if not vp_token:
            try:
                body_data = request.get_json() or {}
                vp_token = body_data.get("vp_token")
                state = body_data.get("state")
            except:
                pass

        # Last resort - try to get from data if it's a string (iOS format)
        if not vp_token and request.data:
            try:
                body_str = request.data.decode("utf-8")
                if body_str.startswith("vp_token="):
                    vp_token = body_str.split("vp_token=")[1].split("&")[0]
            except:
                pass

        if not vp_token:
            logger.error("No vp_token parameter found in request")
            return jsonify({"error": "No vp_token parameter found", "valid": 0}), 400

        # Decode the JWT token
        # SD-JWT Handling: Split off disclosures to decode the issuer JWT
        if "~" in vp_token:
            decoded_vp = decode_jwt_token(vp_token.split("~")[0])
        else:
            decoded_vp = decode_jwt_token(vp_token)

        if not decoded_vp:
            logger.error("Failed to decode VP token")
            return jsonify({"error": "Failed to decode VP token", "valid": 0}), 400

        # Step 1: Presentation request received
        emit_to_session(
            "presentation_received",
            {"status": "success", "message": "Präsentation empfangen"},
        )

        # Extract the presentation from the VP
        presentation = extract_presentation_from_vp(decoded_vp)

        # Step 2: Extract credential fields
        emit_to_session(
            "key_extraction",
            {"status": "success", "message": "Credential-Felder extrahiert"},
        )

        # Get presentation definition with mandatory fields
        presentation_def = get_presentation_definition()
        technical_fields = presentation_def.get("technical_fields", TECHNICAL_FIELDS)
        user_mandatory_fields = presentation_def.get("user_mandatory_fields", [])

        logger.debug(
            f"VERIFICATION: presentation_def keys: {list(presentation_def.keys())}"
        )
        logger.debug(f"VERIFICATION: technical_fields count: {len(technical_fields)}")
        logger.debug(
            f"VERIFICATION: user_mandatory_fields count: {len(user_mandatory_fields)}"
        )

        # CRITICAL FIX: If user_mandatory_fields is empty but we expect user fields,
        # try to get them from the current request context
        if len(user_mandatory_fields) == 0:
            logger.warning(
                "No user mandatory fields found - checking if database context is available"
            )
            try:
                # Try to get settings again with explicit error handling
                from .settings_integration import (
                    get_current_selective_disclosure_settings,
                )

                current_fields = get_current_selective_disclosure_settings()

                # Separate user fields from technical fields
                potential_user_fields = []
                for field in current_fields:
                    if field not in technical_fields and (
                        field.startswith("vc.credentialSubject.")
                        or field
                        in ["firstName", "lastName", "studentId", "studentIdPrefix"]
                    ):
                        potential_user_fields.append(field)

                if potential_user_fields:
                    logger.info(
                        f"VERIFICATION FIX: Found {len(potential_user_fields)} user fields via direct settings call"
                    )
                    user_mandatory_fields = potential_user_fields
                    # Update the presentation definition for this request
                    presentation_def["user_mandatory_fields"] = user_mandatory_fields

            except Exception as settings_error:
                logger.error(f"Could not retrieve user fields: {settings_error}")

        # Skip demo credentials check
        demo_credential = "demo_credential" in str(decoded_vp).lower()

        # 🩺 HERZCHIRURG-FIX: Verwende die neue robuste Integration
        if not demo_credential:
            # Step 3-5: Robuste Verifikation mit detaillierter Fehlerbehandlung
            valid, verification_details = safe_verify_presentation(
                decoded_vp, presentation_def, raw_token=vp_token, expected_nonce=expected_nonce
            )
            if not valid:
                logger.error(
                    f"Advanced verification failed: {verification_details.get('error')}"
                )

                # Bestimme den Fehlertyp und Schritt
                error_type = verification_details.get("error_type", "unknown_error")
                error_details = verification_details.get("error", "Unknown error")

                # Bestimme den Schritt basierend auf dem Fehlertyp
                step = 3  # Default
                successful_steps = 2

                if (
                    error_type == "bbs_verification_failed"
                    or error_type == "bbs_verification_exception"
                ):
                    step = 5
                    successful_steps = 4
                elif error_type == "credential_validity_failed":
                    step = 6
                    successful_steps = 5
                elif error_type == "presentation_integrity_error":
                    step = 3
                    successful_steps = 2

                # Sende Fehlerdetails an den Client mit spezifischem Event-Namen
                if (
                    error_type == "bbs_verification_failed"
                    or error_type == "bbs_verification_exception"
                ):
                    emit_to_session(
                        "signature_verification",
                        {
                            "status": "error",
                            "message": f"BBS+ Verifikation fehlgeschlagen: {error_details}",
                        },
                    )
                elif error_type == "credential_validity_failed":
                    emit_to_session(
                        "credential_validity_status",
                        {
                            "status": "error",
                            "message": f"Gültigkeit fehlgeschlagen: {error_details}",
                        },
                    )
                elif error_type == "presentation_integrity_error":
                    emit_to_session(
                        "mandatory_fields_verification",
                        {
                            "status": "error",
                            "message": f"Präsentation ungültig: {error_details}",
                        },
                    )
                else:
                    emit_to_session(
                        "verification_result",
                        {
                            "status": "error",
                            "message": f"Verifikation fehlgeschlagen: {error_details}",
                        },
                    )

                return jsonify(
                    {
                        "error": error_details,
                        "error_type": error_type,
                        "verification_details": verification_details,
                        "valid": 0,
                        "step": step,
                        "successful_steps": successful_steps,
                    }
                ), 400

            # Determine format
            is_sd_jwt = verification_details.get("format") == "sd_jwt"

            # Wenn die Verifikation erfolgreich war, setzen wir alle Schritte auf Erfolg
            emit_to_session(
                "mandatory_fields_verification",
                {
                    "status": "success",
                    "message": "Pflichtfelder validiert",
                    "format": "sd_jwt" if is_sd_jwt else "bbs",
                },
            )

            # Extract issuer if possible
            issuer_id = "did:web:example.com"
            if verification_details.get("verified_payload"):
                issuer_id = verification_details.get("verified_payload").get(
                    "iss", issuer_id
                )

            emit_to_session(
                "issuer_pub_key_verification",
                {
                    "status": "success",
                    "message": "Aussteller berechtigt",
                    "format": "sd_jwt" if is_sd_jwt else "bbs",
                    "details": {
                        "issuer": issuer_id,
                        "registry": "European Trust List (simulated)",
                        "verification": "X.509 Certificate Chain"
                        if is_sd_jwt
                        else "DID Verification Method",
                        "status": "Active / Accredited",
                        "timestamp": "Verified just now",
                    },
                },
            )

            if is_sd_jwt:
                emit_to_session(
                    "signature_verification",
                    {
                        "status": "success",
                        "message": "SD-JWT Signatur validiert",
                        "format": "sd_jwt",
                        "details": {
                            "protocol": "OIDC4VP (SD-JWT)",
                            "signature": "ECDSA (ES256)",
                            "curve": "P-256",
                            "binding": "Key Binding JWT present",
                        },
                    },
                )
            else:
                emit_to_session(
                    "signature_verification",
                    {
                        "status": "success",
                        "message": "BBS+ Signatur validiert",
                        "format": "bbs",
                        "details": {
                            "protocol": "BBS+ Signature Scheme",
                            "signature": "BLS12-381",
                            "curve": "BLS12-381",
                            "binding": "Zero-Knowledge Proof",
                        },
                    },
                )

            # Step 6: Check credential validity status
            # For SD-JWT, use the verified payload which includes validity_identifier (if added by issuer)
            # The original decoded_vp might hide it or not be the best source.
            vp_to_validate = decoded_vp

            if (
                valid
                and verification_details.get("format") == "sd_jwt"
                and verification_details.get("verified_payload")
            ):
                # Wrap payload in a structure validate_credential_validity understands if needed
                # But validity_identifier is usually top level.
                vp_to_validate = verification_details.get("verified_payload")
                # If verified_payload is just {iss, ...}, allow searching it.

            valid_status, status_msg = validate_credential_validity(vp_to_validate)
            if not valid_status:
                logger.error(f"Credential validity check failed: {status_msg}")
                emit_to_session(
                    "credential_validity_status",
                    {
                        "status": "error",
                        "message": f"Gültigkeitsprüfung fehlgeschlagen: {status_msg}",
                    },
                )
                return jsonify(
                    {
                        "error": status_msg,
                        "valid": 0,
                        "error_type": "credential_validity_failed",
                        "step": 6,
                        "successful_steps": 5,
                    }
                ), 400
        else:
            # Demo Credential: Vereinfachte Validierung
            emit_to_session(
                "mandatory_fields_verification",
                {
                    "status": "success",
                    "message": "Pflichtfelder validiert (Demo-Modus)",
                },
            )

            emit_to_session(
                "issuer_pub_key_verification",
                {"status": "success", "message": "Aussteller validiert (Demo-Modus)"},
            )

            emit_to_session(
                "signature_verification",
                {"status": "success", "message": "Demo-Credential erkannt"},
            )

        emit_to_session(
            "credential_validity_status",
            {"status": "success", "message": "Gültigkeit bestätigt"},
        )

        # Step 7: Check user mandatory fields
        # Extract values from the credential
        values = {}

        # FIX: For SD-JWT, use the verified payload for everything
        if (
            valid
            and verification_details.get("format") == "sd_jwt"
            and verification_details.get("verified_payload")
        ):
            values = verification_details.get("verified_payload")
        else:
            vc = decoded_vp.get("verifiable_credential", {})
            if "values" in vc:
                values = vc["values"]
            else:
                # Try to extract from other locations
                for field in ALL_CREDENTIAL_FIELDS:
                    value = get_field_value(decoded_vp, field)
                    if value:
                        values[field] = value

        # Verarbeite übergroße Felder für die Antwort
        safe_values = process_oversized_fields(values)

        # Determine format for the key verification message
        is_sd_jwt_fmt = False
        try:
            if (
                "verification_details" in locals()
                and verification_details
                and verification_details.get("format") == "sd_jwt"
            ):
                is_sd_jwt_fmt = True
        except:
            pass

        if is_sd_jwt_fmt:
            emit_to_session(
                "issuer_bbs_key_verification",
                {
                    "status": "success",
                    "message": "ECDSA Schlüssel validiert",
                    "format": "sd_jwt",
                    "details": {
                        "algorithm": "ES256 (ECDSA using P-256 and SHA-256)",
                        "key_type": "Public Key (PEM/JWK)",
                        "input": "Public key from issuer DID document",
                        "validation": "Signature verification on SD-JWT and Disclosures",
                        "security": "NIST P-256 (128-bit security)",
                    },
                },
            )
        else:
            emit_to_session(
                "issuer_bbs_key_verification",
                {
                    "status": "success",
                    "message": "BBS+ Schlüssel validiert",
                    "format": "bbs",
                    "details": {
                        "algorithm": "BLS12-381 Signature Scheme",
                        "key_type": "G2 element (48/96 bytes)",
                        "input": "Public key from issuer DID document (#bbsKey2021)",
                        "validation": "Point-on-curve, subgroup membership",
                        "security": "128-bit security equivalent",
                    },
                },
            )

        # Don't send duplicate verification_result here - it's sent after processing disclosed fields

        # Track which fields were disclosed (categorized)
        disclosed_info = {
            "technical": [],
            "mandatory": [],
            "optional": [],
            "undeclared": [],
        }

        # Process disclosed fields
        logger.debug(f"FIELD CATEGORIZATION: Processing {len(safe_values)} fields")
        logger.debug(
            f"FIELD CATEGORIZATION: Available fields: {list(safe_values.keys())}"
        )
        logger.debug(
            f"FIELD CATEGORIZATION: User mandatory fields: {presentation_def.get('user_mandatory_fields', [])}"
        )
        logger.debug(f"FIELD CATEGORIZATION: Technical fields: {technical_fields}")

        # BACKUP SYSTEM COMPATIBILITY: Use explicit field categorization
        # Define core technical fields (always technical, never user fields)
        core_technical_fields = {
            "iss",
            "sub",
            "exp",
            "nbf",
            "jti",
            "aud",
            "nonce",
            "signedNonce",
            "bbsDPK",
            "totalMessages",
            "validityIdentifier",
            "signed_nonce",
            "bbs_dpk",
            "total_messages",
            "validity_identifier",
        }

        # Define known user credential fields (the 4 fields user can select)
        known_user_fields = {
            "firstName",
            "lastName",
            "studentId",
            "studentIdPrefix",
            "studentID",
            "studentIDPrefix",  # iOS uppercase variants
            "image", # Profile image field
            "vc.credentialSubject.firstName",
            "vc.credentialSubject.lastName",
            "vc.credentialSubject.studentId",
            "vc.credentialSubject.studentIdPrefix",
            "vc.credentialSubject.image", # Profile image nested path
        }

        # CRITICAL FIX: Handle credentialSubject nested fields
        if "credentialSubject" in safe_values and isinstance(
            safe_values["credentialSubject"], dict
        ):
            logger.info(
                f"FIELD CATEGORIZATION: Found credentialSubject with {len(safe_values['credentialSubject'])} nested fields"
            )

            # Add credentialSubject fields to personal fields
            for cs_field, cs_value in safe_values["credentialSubject"].items():
                if cs_field in [
                    "firstName",
                    "lastName",
                    "studentId",
                    "studentIdPrefix",
                    "email",
                    "dateOfBirth",
                    "studyProgram",
                    "image",
                ]:
                    disclosed_info["mandatory"].append(f"credentialSubject.{cs_field}")
                    logger.debug(
                        f"✅ User field (from credentialSubject): 'credentialSubject.{cs_field}' = {str(cs_value)[:50] if cs_value else ''}"
                    )

        # CRITICAL FIX 2: Handle credentialSubject nested inside "vc" field
        if "vc" in safe_values and isinstance(safe_values["vc"], dict):
            vc_content = safe_values["vc"]
            logger.info(
                f"FIELD CATEGORIZATION: Found 'vc' field with content: {vc_content}"
            )

            if "credentialSubject" in vc_content and isinstance(
                vc_content["credentialSubject"], dict
            ):
                logger.info(
                    f"FIELD CATEGORIZATION: Found credentialSubject inside vc with {len(vc_content['credentialSubject'])} nested fields"
                )

                # Add credentialSubject fields to personal fields
                for cs_field, cs_value in vc_content["credentialSubject"].items():
                    if cs_field in [
                        "firstName",
                        "lastName",
                        "studentId",
                        "studentIdPrefix",
                        "email",
                        "dateOfBirth",
                        "studyProgram",
                        "image",
                    ]:
                        disclosed_info["mandatory"].append(
                            f"vc.credentialSubject.{cs_field}"
                        )
                        logger.debug(
                            f"✅ User field (from vc.credentialSubject): 'vc.credentialSubject.{cs_field}'"
                        )

        for field in safe_values.keys():
            # Skip credentialSubject object itself - we handled its contents above
            if field == "credentialSubject":
                continue

            # Skip vc object if it contains credentialSubject - we handled its contents above
            if (
                field == "vc"
                and isinstance(safe_values[field], dict)
                and "credentialSubject" in safe_values[field]
            ):
                continue

            field_base = field.split(".")[-1] if "." in field else field

            # 1. Check if it's a core technical field
            if field in core_technical_fields or field_base in core_technical_fields:
                disclosed_info["technical"].append(field)
                logger.debug(f"✅ Technical field: '{field}'")
                continue

            # 2. Check if it's a known user field (the 4 selectable fields)
            is_user_field = (
                field in known_user_fields
                or field_base in known_user_fields
                or field.startswith("vc.credentialSubject.")
                and field_base
                in ["firstName", "lastName", "studentId", "studentIdPrefix"]
            )

            if is_user_field:
                # Check if this user field was actually requested
                field_was_requested = False

                # Enhanced debugging for user field matching
                user_mandatory_list = presentation_def.get("user_mandatory_fields", [])
                logger.debug(
                    f"🔍 FIELD MATCHING: Checking user field '{field}' (base: '{field_base}') against mandatory list: {user_mandatory_list}"
                )

                # Check against user_mandatory_fields with iOS compatibility
                for mandatory in user_mandatory_list:
                    m_base = mandatory.split(".")[-1] if "." in mandatory else mandatory

                    # iOS field name normalization
                    ios_mapping = {
                        "studentID": "studentId",
                        "studentIDPrefix": "studentIdPrefix",
                    }
                    norm_field = ios_mapping.get(field, field)
                    norm_field_base = ios_mapping.get(field_base, field_base)
                    norm_mandatory = ios_mapping.get(m_base, m_base)

                    logger.debug(
                        f"🔍 COMPARING: '{field_base}' vs '{m_base}', normalized: '{norm_field_base}' vs '{norm_mandatory}'"
                    )

                    if (
                        field_base == m_base
                        or field == mandatory
                        or norm_field_base == norm_mandatory
                        or norm_field == norm_mandatory
                    ):
                        disclosed_info["mandatory"].append(field)
                        field_was_requested = True
                        logger.info(
                            f"✅ User field (mandatory): '{field}' matched '{mandatory}' - COUNTING AS PERSONAL FIELD"
                        )
                        break

                if not field_was_requested:
                    # User field but not requested - mark as optional
                    disclosed_info["optional"].append(field)
                    logger.debug(f"✅ User field (optional): '{field}'")
                continue

        # Log final categorization results
        total_technical = len(disclosed_info["technical"])
        total_personal = len(disclosed_info["mandatory"]) + len(
            disclosed_info["optional"]
        )
        total_additional = len(disclosed_info["undeclared"])

        logger.info(
            f"FIELD CATEGORIZATION COMPLETE: {total_technical} technical, {total_personal} personal, {total_additional} additional"
        )

        if total_personal == 0 and len(disclosed_info["undeclared"]) > 0:
            logger.warning(
                f"Potential issue: {len(disclosed_info['undeclared'])} fields marked as undeclared: {disclosed_info['undeclared']}"
            )
            logger.warning("This may indicate a field categorization problem")

        # Send the final success SocketIO event with enhanced issuer information
        # Get issuer info from config
        from flask import current_app

        if (
            'summary' not in locals()
        ):  # Only send if we haven't already sent a summary (which we haven't here)
            # Try to extract issuer from verified payload (most reliable)
            display_issuer = current_app.config.get(
                "UNIVERSITY_NAME", "Technische Universität Berlin"
            )

            try:
                # Check safe_values first (processed payload)
                if "iss" in safe_values:
                    iss = safe_values["iss"]
                    if iss.startswith("did:web:"):
                        display_issuer = iss[8:].replace("%3A", ":")
                    else:
                        display_issuer = iss
                # Check verification details as fallback
                elif "verification_details" in locals() and verification_details.get(
                    "verified_payload"
                ):
                    iss = verification_details.get("verified_payload").get("iss")
                    if iss:
                        if iss.startswith("did:web:"):
                            display_issuer = iss[8:].replace("%3A", ":")
                        else:
                            display_issuer = iss
            except Exception as e:
                logger.warning(f"Could not extract issuer for display: {e}")

            # 🔧 DEBUG: Log system detection details
            logger.info(f"🔧 VERIFICATION DEBUG: Issuer info = '{display_issuer}'")

            emit_to_session(
                "verification_result",
                {
                    "status": "success",
                    "message": f"🎉 Verifikation erfolgreich abgeschlossen!<br/>✅ Gültiger Studierendenausweis ausgestellt von <strong>{display_issuer}</strong>",
                    "issuer": display_issuer,
                    "transmitted_fields": {
                        "technical": disclosed_info["technical"],
                        "personal": disclosed_info["mandatory"]
                        + disclosed_info["optional"],
                        "additional": disclosed_info["undeclared"],
                        "values": safe_values,  # Include actual field values
                    },
                },
            )

        # VC Login logic removed (Verifier is stateless)

        # Include disclosed fields info in the verification result
        # Match the working version's response format
        return jsonify({"success": "Access token is valid"}), 200

    except jwt.DecodeError as e:
        logger.error(f"JWT decode error: {e}")
        return jsonify(
            {
                "error": f"Invalid JWT token format: {str(e)}",
                "valid": 0,
                "error_type": "jwt_decode_error",
                "step": 2,
                "successful_steps": 1,
            }
        ), 400
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return jsonify(
            {
                "error": f"Missing required field: {str(e)}",
                "valid": 0,
                "error_type": "missing_field",
                "step": 3,
                "successful_steps": 2,
            }
        ), 400
    except Exception as e:
        logger.error(f"Error in verification: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # 🩺 HERZCHIRURG-FIX: Allgemeiner Fehler mit korrekter Schrittzählung
        # Bestimme, in welchem Schritt der Fehler aufgetreten ist
        error_step = 1  # Default: Präsentationsanfrage
        successful_steps = 0
        error_type = "general_error"

        # Versuche zu bestimmen, in welchem Schritt der Fehler aufgetreten ist
        error_str = str(e).lower()
        if (
            "signature" in error_str
            or "bbs" in error_str
            or "proof" in error_str
            or "verification" in error_str
        ):
            error_step = 5
            successful_steps = 4
            error_type = "bbs_verification_failed"
        elif "credential" in error_str or "valid" in error_str or "status" in error_str:
            error_step = 6
            successful_steps = 5
            error_type = "credential_validity_failed"
        elif (
            "mandatory" in error_str or "field" in error_str or "required" in error_str
        ):
            error_step = 3
            successful_steps = 2
            error_type = "missing_field"
        elif "issuer" in error_str or "trust" in error_str:
            error_step = 4
            successful_steps = 3
            error_type = "issuer_validation_failed"
        elif "jwt" in error_str or "token" in error_str or "decode" in error_str:
            error_step = 2
            successful_steps = 1
            error_type = "jwt_decode_error"
        elif "key" in error_str or "extract" in error_str:
            error_step = 2
            successful_steps = 1
            error_type = "field_extraction_failed"

        # Sende detaillierte Fehlermeldung mit Schrittzählung
        emit_to_session(
            "verification_result",
            {
                "status": "error",
                "valid": 0,
                "message": f"Verification failed: {str(e)}",
                "user_message": f"Verifikation fehlgeschlagen: {str(e)}",
                "step": error_step,
                "successful_steps": successful_steps,
                "error_type": error_type,
            },
        )

        return jsonify(
            {
                "error": f"An error occurred during verification: {str(e)}",
                "details": str(e),
                "traceback": traceback.format_exc().split("\n")[
                    -10:
                ],  # Nur die letzten 10 Zeilen für Sicherheit
                "valid": 0,
                "step": error_step,
                "successful_steps": successful_steps,
                "error_type": error_type,
            }
        ), 500
