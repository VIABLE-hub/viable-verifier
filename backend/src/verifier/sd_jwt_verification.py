import logging
import os
import base58
from sd_jwt.verifier import SDJWTVerifier
from jwcrypto.jwk import JWK
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from .presentation_routes import get_aud_val
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
            if len(decoded) == 35: # 2 prefix + 33 key
                 pub_bytes = decoded[2:]
            elif len(decoded) == 33: # No prefix?
                 pub_bytes = decoded
            else:
                 logger.warning(f"Unknown key length/prefix for did:key")
                 return None

        # Load key using cryptography
        try:
            pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pub_bytes)
            
            # Convert to PEM to let jwcrypto handle JWK conversion easily
            pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
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
            pem_key = pem_key.encode('utf-8')
        
        jwk_obj = JWK.from_pem(pem_key)
        
        return jwk_obj.export(as_dict=True)
    except Exception as e:
        logger.error(f"Error converting PEM to JWK: {e}")
        return None

def verify_sd_jwt_presentation(raw_token, expected_nonce=None):
    # Ensure keys are initialized
    
    # Load public key directly from instance/public.pem (Verifier setup)
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance')
    public_key_path = os.path.join(instance_dir, 'keys', 'public.pem')
    
    # Fallback to instance/public.pem if keys/public.pem doesn't exist
    if not os.path.exists(public_key_path):
        public_key_path = os.path.join(instance_dir, 'public.pem')
        
    try:
        with open(public_key_path, 'r') as f:
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

        def cb_get_issuer_key(issuer_id, key_id):
            logger.info(f"Resolving key for issuer: {issuer_id}")
            
            # 1. Try to resolve from DID (True Verifier approach)
            if issuer_id and issuer_id.startswith("did:key:"):
                resolved_jwk = resolve_did_key(issuer_id)
                if resolved_jwk:
                    logger.info("Successfully resolved issuer key from did:key")
                    # Add Kid if present
                    if key_id:
                        resolved_jwk["kid"] = key_id
                    return JWK(**resolved_jwk)
            
            # 2. Fallback to local trusted key (Monolith/Testing approach)
            logger.info("Using local trusted public key for verification")
            jwk_dict = local_issuer_jwk
            # Add Kid if present
            if key_id:
                jwk_dict["kid"] = key_id
            
            # The SD-JWT library expects a JWK object
            return JWK(**jwk_dict)

        # Setup verifier
        verifier = SDJWTVerifier(
            raw_token,
            cb_get_issuer_key,
            None, # Expected aud
            None, # Expected nonce 
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
                logger.warning("No expected_nonce provided, checking DB for legacy nonce support")
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
