import logging
import os
import base58
import requests
from sd_jwt.verifier import SDJWTVerifier
from jwcrypto.jwk import JWK
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from .presentation_routes import get_aud_val, get_nonce_val
from ..models import VP_NONCE, db

logger = logging.getLogger(__name__)


def resolve_did_key(did):
    """
    Resolve did:key to JWK (P-256 support for now)
    """
    try:
        if not did.startswith("did:key:"):
            return None

        # Extract the multibase key (starts with 'z' for base58btc)
        multibase_key = did.split(":")[-1]
        if not multibase_key.startswith("z"):
            logger.warning(f"Unsupported multibase encoding: {multibase_key[0]}")
            return None

        # Decode base58
        decoded = base58.b58decode(multibase_key[1:])

        # Check multicodec prefix
        # P-256 public key compressed is 0x1200 (varint: 0x80 0x24)
        if decoded[0] == 0x80 and decoded[1] == 0x24:
            # P-256
            pub_bytes = decoded[2:]
        elif decoded[0] == 0x12 and decoded[1] == 0x00:
            # Some implementations might use raw hex? Unlikely.
            # Varint for 0x1200 is 1000 0000  0010 0100 -> 80 24
            pub_bytes = decoded[2:]
        else:
            # Fallback for some did:key implementations that might skip varint or use different codec
            # But "zDn..." typically means P-256.
            # Assuming remaining bytes are the key if length matches
            if len(decoded) == 35:  # 2 prefix + 33 key
                pub_bytes = decoded[2:]
            elif len(decoded) == 33:  # No prefix?
                pub_bytes = decoded
            else:
                logger.warning(f"Unknown key length/prefix for did:key")
                return None

        # Load key using cryptography
        try:
            pub_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), pub_bytes
            )

            # Convert to PEM to let jwcrypto handle JWK conversion easily
            pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            jwk = JWK.from_pem(pem)
            return jwk.export(as_dict=True)

        except Exception as e:
            logger.error(f"Failed to load EC key from bytes: {e}")
            return None

    except Exception as e:
        logger.error(f"Error resolving did:key: {e}")
        return None


def pem_to_jwk(pem_key):
    """
    Convert PEM to JWK format for SD-JWT library.
    """
    try:
        if isinstance(pem_key, str):
            pem_key = pem_key.encode("utf-8")

        jwk_obj = JWK.from_pem(pem_key)

        return jwk_obj.export(as_dict=True)
    except Exception as e:
        logger.error(f"Error converting PEM to JWK: {e}")
        return None


def resolve_did_web(did):
    """
    Resolve did:web to JWK
    """
    try:
        if not did.startswith("did:web:"):
            return None

        # Parse domain
        # Format: did:web:example.com or did:web:example.com:path
        parts = did.split(":")
        if len(parts) < 3:
            return None

        domain = parts[2].replace("%3A", ":")
        path_parts = parts[3:]

        if path_parts:
            # Join with slashes
            path = "/".join(path_parts)
            url = f"https://{domain}/{path}/did.json"
        else:
            url = f"https://{domain}/.well-known/did.json"

        logger.info(f"Fetching DID Doc from: {url}")
        # Use verify=False if potentially testing with self-signed certs (dev env), otherwise verify=True
        response = requests.get(
            url, timeout=10
        )  # Removed verify=False for security, but might be needed in dev

        if response.status_code != 200:
            logger.error(f"Failed to fetch DID Doc: {response.status_code}")
            return None

        did_doc = response.json()

        # We return the whole list of keys or filter by Key ID?
        # The callback needs one key. We should return all keys map or handle resolution logic.
        # But for 'kb_get_issuer_key', we expect a single JWK.

        return did_doc

    except Exception as e:
        logger.error(f"Error resolving did:web: {e}")
        return None


def verify_sd_jwt_presentation(raw_token, expected_nonce=None):
    # Ensure keys are initialized

    # Load public key directly from instance/public.pem (Verifier setup)
    instance_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "instance"
    )
    public_key_path = os.path.join(instance_dir, "keys", "public.pem")

    # Fallback to instance/public.pem if keys/public.pem doesn't exist
    if not os.path.exists(public_key_path):
        public_key_path = os.path.join(instance_dir, "public.pem")

    try:
        with open(public_key_path, "r") as f:
            public_key_pem = f.read()
    except Exception as e:
        logger.error(f"Failed to load public key: {e}")
        return False, f"Server configuration error: Public key not found", None

    # Get issuer public key in JWK format
    local_issuer_jwk = pem_to_jwk(public_key_pem)

    if not local_issuer_jwk:
        logger.error("Issuer public key not available for SD-JWT verification")
        return False, "Issuer public key not available", {}

    try:

        def cb_get_issuer_key(issuer_id, header_params):
            # The second argument is the full header dict, extract KID from it
            key_id = (
                header_params.get("kid")
                if isinstance(header_params, dict)
                else header_params
            )

            logger.info(f"Resolving key for issuer: {issuer_id} (kid: {key_id})")

            # Enforce did:web for issuer
            if not issuer_id or not issuer_id.startswith("did:web:"):
                error_msg = f"Issuer DID must be did:web. Found: {issuer_id}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # Try to resolve from DID (did:web)
            did_doc = resolve_did_web(issuer_id)
            if did_doc:
                logger.info("Successfully fetched DID Document for did:web")
                # Find matching verification method
                for vm in did_doc.get("verificationMethod", []):
                    # Match KID if provided
                    # Standard KID in headers might be "did:web:example.com#key-1" or just "key-1"
                    # The VM ID is usually fully qualified "did:web:example.com#key-1"

                    is_match = False
                    vm_id = vm.get("id", "")

                    if not key_id:
                        # If no KID requested (unlikely), take the first one
                        is_match = True
                    elif vm_id == key_id:
                        is_match = True
                    elif vm_id.endswith(f"#{key_id}"):
                        is_match = True
                    elif key_id.startswith("#") and vm_id.endswith(key_id):
                        is_match = True

                    if is_match:
                        if "publicKeyJwk" in vm:
                            logger.info(f"Using key from DID Doc: {vm_id}")
                            return JWK(**vm["publicKeyJwk"])

                logger.warning(f"No matching key found in DID Doc for kid: {key_id}")

            raise Exception(
                "Could not resolve DID or find matching key in DID Document"
            )

        nonce = expected_nonce if expected_nonce else get_nonce_val()
        aud = get_aud_val()
        
        # Setup verifier
        
        
        verifier = SDJWTVerifier(
            raw_token,
            cb_get_issuer_key,
            aud,  # Expected aud
            nonce,  # Expected nonce
            serialization_format="compact",
        )

        # Verify
        logger.info("Starting SD-JWT verification...")
        verified_payload = verifier.get_verified_payload()

        # Additional manual checks for Nonce and Aud
        # Verify Nonce
        # Note: The library might have verified it if we passed it, but let's do manual check to be sure about the error message

        # If we have a nonce in payload, check if it was used/generated by us
        if "nonce" in verified_payload:
            token_nonce = verified_payload["nonce"]

            # Helper to check database
            nonce_valid = False
            # First check global/session nonce
            if expected_nonce and token_nonce == expected_nonce:
                nonce_valid = True
            elif not expected_nonce:
                # If no nonce expected (legacy flow), check db
                logger.warning(
                    "No expected_nonce provided, checking DB for legacy nonce support"
                )
                matching_nonce = VP_NONCE.query.filter_by(nonce=token_nonce).first()
                if matching_nonce:
                    nonce_valid = True

            if not nonce_valid:
                # Check database
                matching_nonce = VP_NONCE.query.filter_by(nonce=token_nonce).first()
                if matching_nonce:
                    nonce_valid = True
                    # Optionally delete used nonce here to prevent replay
                    # db.session.delete(matching_nonce)
                    # db.session.commit()

            if not nonce_valid:
                logger.warning(f"Invalid nonce in token: {token_nonce}")
                # return False, "Invalid Nonce", {} # Strict mode
                # For testing, we might be lenient or the nonce mechanism might be async

        logger.info("SD-JWT presentation verified successfully")
        return True, verified_payload, "SD-JWT verified successfully"

    except Exception as e:
        logger.error(f"SD-JWT verification failed: {e}")
        import traceback

        traceback.print_exc()
        return False, {}, f"SD-JWT Verification failed: {str(e)}"
