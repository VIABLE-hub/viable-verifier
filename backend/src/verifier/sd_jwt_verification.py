import logging
from sd_jwt.verifier import SDJWTVerifier
from jwcrypto.jwk import JWK
from ..issuer import issuer
from ..issuer.jwks import pem_to_jwk
from .presentation_routes import get_aud_val, get_nonce_val

from ..models import VP_NONCE, db

logger = logging.getLogger(__name__)


def verify_sd_jwt_presentation(raw_token):
    # Ensure keys are initialized

    if not issuer.public_key:
        logger.info("SD-JWT: Issuer keys not initialized. Attemping initialization...")
        try:
            issuer.initialize_keys()
        except Exception as e:
            logger.warning(f"SD-JWT: Failed to initialize issuer keys: {e}")

    if not issuer.public_key:
        logger.error("Issuer public key not available for SD-JWT verification")
        return False, "Issuer public key not available", {}
    try:

        def cb_get_issuer_key(issuer_id, key_id):
            # Convert our global PEM public key to JWK
            # pem_to_jwk handles string or object
            jwk_dict = pem_to_jwk(issuer.public_key)
            # Add Kid if present
            if key_id:
                jwk_dict["kid"] = key_id
            elif issuer.issuer_kid:
                jwk_dict["kid"] = issuer.issuer_kid
            # Return JWK object as expected by sd-jwt/jwcrypto
            return JWK(**jwk_dict)

        # these come from verifier to enable holder-key-binding
        nonce = get_nonce_val()
        aud = get_aud_val()

        nonce_row = VP_NONCE.query.filter_by(nonce=nonce).first()
        if nonce_row.used:
            raise Exception("Nonce already used (replay detected)")
        verifier = SDJWTVerifier(
            raw_token,
            cb_get_issuer_key=cb_get_issuer_key,
            expected_aud=aud,
            expected_nonce=nonce,
        )
        nonce_row.mark_used()
        db.session.commit()
        payload = verifier.get_verified_payload()
        logger.info(f"SD-JWT verification successful. Payload keys: {payload.keys()}")
        logger.info(f"SD-JWT verification successful. Payload: {payload}")
        return True, "SD-JWT Verified", payload

    except Exception as e:
        logger.error(f"SD-JWT Verification exception: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False, f"SD-JWT Verification failed: {str(e)}", {}
