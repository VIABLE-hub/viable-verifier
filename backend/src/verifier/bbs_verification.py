"""
BBS+ Verifikationslogik für den Verifier.

Enthält Funktionen zur kryptografischen Verifikation von BBS+ Beweisen.
"""

import json
import base64
import os
import importlib.util
from logging import getLogger
from flatten_json import flatten
from ..models import VP_NONCE, db
from .presentation_routes import get_nonce_val 

logger = getLogger("LOGGER")

# Load BBS+ core from the backend directory
bbs_core_path = os.path.join(os.path.dirname(__file__), "..", "..", "bbs_core.py")
bbs_core_path = os.path.abspath(bbs_core_path)
logger.debug(f"Loading BBS+ core from: {bbs_core_path}")

if not os.path.exists(bbs_core_path):
    # Fallback to backend directory
    bbs_core_path = os.path.join(os.path.dirname(__file__), "..", "..", "bbs_core.py")
    bbs_core_path = os.path.abspath(bbs_core_path)
    logger.debug(f"Fallback: Loading BBS+ core from: {bbs_core_path}")

if not os.path.exists(bbs_core_path):
    # Final fallback to project root
    bbs_core_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "bbs_core.py"
    )
    bbs_core_path = os.path.abspath(bbs_core_path)
    logger.debug(f"Final fallback: Loading BBS+ core from: {bbs_core_path}")

if not os.path.exists(bbs_core_path):
    raise ImportError(f"BBS+ core library not found. Searched paths: {bbs_core_path}")

spec = importlib.util.spec_from_file_location("bbs_core", bbs_core_path)
bbs_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbs_core)

logger = getLogger("LOGGER")


def handle_oversized_field(field_key, value, max_length=10000):
    """
    Behandelt zu große Felder wie Base64-Bilder

    Args:
        field_key: Schlüssel des Feldes
        value: Wert des Feldes
        max_length: Maximale erlaubte Länge

    Returns:
        Sicherer, verarbeitbarer Wert
    """
    if isinstance(value, str) and len(value) > max_length:
        logger.warning(
            f"Feld '{field_key}' ist zu groß ({len(value)} Zeichen), wird gekürzt"
        )
        # Für Base64-Bilder oder andere große Felder: Hash oder Präfix verwenden
        # damit es immer noch identifizierbar, aber weniger speicherintensiv ist
        return f"OVERSIZED_FIELD_PREFIX_{value[:100]}..."
    return value


def verify_bbs_proof(decoded_vp, mandatory_fields=None):
    """
    Verifiziert einen BBS+ Beweis aus einer Verifiable Presentation

    Args:
        decoded_vp: Das dekodierte VP-Objekt
        mandatory_fields: Liste der Pflichtfelder, die im Beweis enthalten sein müssen

    Returns:
        (bool, str): (True, "Success") bei erfolgreicher Verifikation,
                    (False, "Error message") bei Fehlern
    """
    try:
        logger.debug("🔹 ====== BBS+ VERIFICATION BEGINNING ======")

        # Helper function for robust Base64 decoding
        def safe_b64decode(data):
            """Safely decode base64 data, handling padding issues."""
            if not isinstance(data, str):
                data = str(data)

            # Remove any whitespace
            data = data.strip()

            # Add padding if needed
            missing_padding = len(data) % 4
            if missing_padding:
                data += "=" * (4 - missing_padding)

            try:
                return base64.b64decode(data)
            except Exception as e:
                logger.error(f"Base64 decode error for data: {data[:50]}... Error: {e}")
                raise

        # Extract the VC from the decoded VP
        vc = decoded_vp.get("verifiable_credential", {})
        if not vc:
            logger.error("No verifiable_credential found in VP")
            return False, "No verifiable_credential found in VP"

        # Get the values (revealed fields) from the credential
        values = vc.get("values", {})
        if not values:
            logger.error("No values found in verifiable credential")
            return False, "No values found in verifiable credential"

        logger.info("=== RECEIVED FIELDS FROM iOS APP ===")
        logger.info(f"Available fields: {list(values.keys())}")
        for key, value in values.items():
            if isinstance(value, dict):
                logger.info(
                    f"Field '{key}': [nested object with keys: {list(value.keys())}]"
                )
            elif isinstance(value, str) and len(value) > 100:
                logger.info(f"Field '{key}': {value[:100]}...")
            else:
                logger.info(f"Field '{key}': {value}")
        logger.info("=== END RECEIVED FIELDS ===")

        # Extract BBS+ metadata - check both locations (new structure and legacy)
        bbs_dpk = None
        total_messages = None

        # New structure: BBS+ metadata in VC root
        if "bbs_dpk" in vc:
            bbs_dpk = vc["bbs_dpk"]
        elif "bbsDPK" in vc:
            bbs_dpk = vc["bbsDPK"]
        # Legacy fallback: in values
        elif "bbs_dpk" in values:
            bbs_dpk = values["bbs_dpk"]
        elif "bbsDPK" in values:
            bbs_dpk = values["bbsDPK"]

        if "total_messages" in vc:
            total_messages = vc["total_messages"]
        elif "totalMessages" in vc:
            total_messages = vc["totalMessages"]
        # Legacy fallback: in values
        elif "total_messages" in values:
            total_messages = values["total_messages"]
        elif "totalMessages" in values:
            total_messages = values["totalMessages"]

        if not bbs_dpk:
            logger.error("No BBS+ distributed public key (DPK) found in VP")
            return False, "No BBS+ distributed public key (DPK) found"

        if not total_messages:
            logger.error("No total_messages count found in VP")
            return False, "No total_messages count found"

        total_messages = int(total_messages)
        logger.info(f"🔹 BBS+ DPK found: {bbs_dpk[:30]}...")
        logger.info(f"🔹 Total messages: {total_messages}")

        # Extract the proof from the VC
        proof = vc.get("proof", "")
        if not proof:
            logger.error("No proof found in the verifiable credential")
            return False, "No proof found in the verifiable credential"

        # Extract nonce and proof_req
        nonce = vc.get("nonce", "")
        proof_req = vc.get("proof_req", "")

        if not nonce:
            logger.error("No nonce found in the verifiable credential")
            return False, "No nonce found in the verifiable credential"

        if not proof_req:
            logger.error("No proof_req found in the verifiable credential")
            return False, "No proof_req found in the verifiable credential"

        logger.debug(f"🔹 Proof field value: {proof[:100]}...")
        logger.debug(f"🔹 Nonce field value: {nonce}")
        logger.debug(f"🔹 Proof_req field value: {proof_req[:100]}...")

        # 🚨 CRITICAL INSIGHT: The iOS wallet sends UNFLATTENED values but the proof
        # was created from FLATTENED messages. We need to recreate the exact messages
        # that were disclosed based on what iOS actually revealed.

        # The iOS logs show it creates messages from flattened JWT and reveals specific indices
        # But then it unflattens the structure before sending to verifier

        # Exclude BBS+ metadata from disclosed values
        excluded_bbs_fields = {"bbs_dpk", "bbsDPK", "total_messages", "totalMessages"}
        disclosed_values_raw = {
            k: v for k, v in values.items() if k not in excluded_bbs_fields
        }

        # The critical fix: We need to FLATTEN the disclosed values to match what was used
        # during proof generation
        disclosed_values_flat = {}

        # First, handle top-level fields that don't need flattening
        for key, value in disclosed_values_raw.items():
            if key == "vc" and isinstance(value, dict):
                # Flatten the VC structure
                flattened_vc = flatten(value, ".")
                for flat_key, flat_value in flattened_vc.items():
                    disclosed_values_flat[f"vc.{flat_key}"] = flat_value
            elif key == "signedNonce":
                # Map camelCase to snake_case as used by issuer
                disclosed_values_flat["signed_nonce"] = value
            elif key == "validityIdentifier":
                # Map camelCase to snake_case as used by issuer
                disclosed_values_flat["validity_identifier"] = value
            else:
                # Keep other fields as-is
                disclosed_values_flat[key] = value

        logger.info(
            f"🔹 Flattened disclosed values: {len(disclosed_values_flat)} fields"
        )
        logger.debug(
            f"🔹 Flattened field names: {sorted(disclosed_values_flat.keys())}"
        )

        # Create messages in the EXACT format used by the issuer
        disclosed_messages = []
        for key in sorted(disclosed_values_flat.keys()):
            value = disclosed_values_flat[key]
            # Create message exactly as issuer does
            message = json.dumps(
                {key: value}, ensure_ascii=False, separators=(",", ":")
            )
            disclosed_messages.append(message)
            logger.debug(f"🔹 Created message: {message}")

        logger.info(
            f"🔹 Created {len(disclosed_messages)} disclosed messages for BBS+ verification"
        )

        # Log first few messages for debugging
        for i, msg in enumerate(disclosed_messages[:5]):
            logger.debug(f"   - Disclosed[{i}]: {msg}")

        logger.info(f"🔹 BBS+ verification parameters:")
        logger.info(f"   - Proof: {len(proof)} chars")
        logger.info(f"   - DPK: {len(bbs_dpk)} chars")
        logger.info(f"   - Disclosed messages: {len(disclosed_messages)}")
        logger.info(f"   - Total credential messages: {total_messages}")
        logger.info(f"   - Nonce: {len(nonce)} chars")
        logger.info(f"   - Proof request: {len(proof_req)} chars")

        # 🚨 CRITICAL: Decode base64 to bytes for crypto parameters
        try:
            proof_bytes = safe_b64decode(proof)
            nonce_bytes = safe_b64decode(nonce)
            proof_req_bytes = safe_b64decode(proof_req)
            dpk_bytes = safe_b64decode(bbs_dpk)
        except Exception as e:
            logger.error(f"Failed to decode Base64 values: {e}")
            return False, f"Failed to decode Base64 values: {e}"

        try:
            # The BBS+ library handles the selective disclosure mapping internally
            # through the proof_request which contains the indices that were revealed

            initial_nonce = get_nonce_val()  # this is only used to avoid replayable presentation
            nonce_row = VP_NONCE.query.filter_by(nonce=initial_nonce).first()
            if nonce_row.used:
                raise Exception("Nonce already used (replay detected)")
            verify_request = bbs_core.VerifyRequest(
                nonce_bytes,  # Bytes: decoded nonce
                proof_req_bytes,  # Bytes: decoded proof request (contains indices)
                proof_bytes,  # Bytes: decoded proof
                disclosed_messages,  # List of JSON strings for the disclosed fields
                dpk_bytes,  # Bytes: decoded public key
                total_messages,  # Integer: total count (32)
            )
            nonce_row.mark_used()
            db.session.commit()
            logger.debug(f"🔹 VerifyRequest created successfully")

            # Call verification
            result = verify_request.is_valid()
            logger.info(f"🔹 BBS+ verification result: {result} (type: {type(result)})")

            # Check if verification succeeded
            if result == "true":
                logger.info("🔹 BBS+ proof verification successful")
                logger.debug("🔹 ====== BBS+ VERIFICATION COMPLETE ======")
                return True, "BBS+ proof verification successful"
            else:
                logger.error(f"❌ BBS+ proof verification failed: {result}")

                # Add more detailed error information
                if result == "matchin messages to presentation failed":
                    logger.error("❌ The disclosed messages don't match the proof")
                    logger.error(
                        "❌ This indicates the messages format doesn't match what was used during proof generation"
                    )
                    logger.error(
                        f"❌ Disclosed messages count: {len(disclosed_messages)}"
                    )
                    logger.error(f"❌ Expected total messages: {total_messages}")

                    # Log what we're actually verifying
                    logger.error("❌ Disclosed messages being verified:")
                    for i, msg in enumerate(disclosed_messages):
                        logger.error(f"   - Message[{i}]: {msg}")

                logger.debug("🔹 ====== BBS+ VERIFICATION COMPLETE ======")
                return False, f"BBS+ proof verification failed: {result}"
        except Exception as e:
            logger.error(f"Error creating BBS+ VerifyRequest: {str(e)}")
            return False, f"Error creating BBS+ VerifyRequest: {str(e)}"

    except Exception as e:
        logger.error(f"🚨 BBS+ verification failed: {str(e)}")
        logger.debug("🔹 ====== BBS+ VERIFICATION COMPLETE ======")
        return False, f"BBS+ verification failed: {str(e)}"
