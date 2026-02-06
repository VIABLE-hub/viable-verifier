from flask import Flask, request, redirect, jsonify
import jwt
from .offer import generate_nonce
from ..models import VC_AuthorizationCode
from .. import db
import logging

logger = logging.getLogger(__name__)
holder_public_key = ""


def resolve_direct_post(state, id_jwt):
    # Extract the authorization code from the ID token
    if id_jwt:
        try:
            decoded_id_token = jwt.decode(id_jwt, options={"verify_signature": False})
            iss = decoded_id_token.get("iss")
            global holder_public_key
            holder_public_key = did_to_key(iss)

            decoded_id_token = jwt.decode(
                id_jwt, holder_public_key, algorithms=["ES256"], verify=True
            )

            if not iss:
                return jsonify({"error": "Issuer (iss) not found in id_token"}), 400

            logger.info(f"Direct post from issuer: {iss}")

            # Generate a new authorization code
            authorization_code = generate_nonce(8)
            logger.info(f"Generated new authorization code: {authorization_code}")

            # Retrieve the entry from the database - find by client_id and ensure it's not used
            authorization_code_entry = VC_AuthorizationCode.query.filter_by(
                client_id=iss, used=False
            ).first()

            if authorization_code_entry:
                logger.info(
                    f"Found existing entry for client_id {iss}, updating authorization code"
                )
                logger.info(f"Existing entry before update: {authorization_code_entry}")

                # Update the existing entry with the new authorization code
                authorization_code_entry.auth_code = authorization_code

                try:
                    db.session.commit()
                    logger.info(
                        f"Successfully updated authorization code for client_id: {iss}"
                    )
                    logger.info(f"Updated entry: {authorization_code_entry}")
                except Exception as e:
                    logger.error(f"Failed to update authorization code: {e}")
                    db.session.rollback()
                    return jsonify(
                        {"error": "Failed to update authorization code"}
                    ), 500

            else:
                logger.info(
                    f"No unused entry found for client_id {iss}, creating new one"
                )

                # Check if there are any entries for this client (even used ones) for debugging
                all_entries = VC_AuthorizationCode.query.filter_by(client_id=iss).all()
                logger.info(
                    f"All entries for client_id {iss}: {[str(entry) for entry in all_entries]}"
                )

                # Create a new entry - this should ideally not happen if authorization flow is correct
                new_entry = VC_AuthorizationCode(
                    client_id=iss,
                    auth_code=authorization_code,
                    code_challenge=request.json.get("code_challenge")
                    if request.json
                    else None,
                    issuer_state=request.json.get("issuer_state")
                    if request.json
                    else state,
                    used=False,
                )

                try:
                    db.session.add(new_entry)
                    db.session.commit()
                    logger.info(f"Created new authorization code entry: {new_entry}")
                except Exception as e:
                    logger.error(f"Failed to create new authorization code entry: {e}")
                    db.session.rollback()
                    return jsonify(
                        {"error": "Failed to create authorization code"}
                    ), 500

            # Construct the redirect URL
            redirect_url = f"openid://redirect?code={authorization_code}&state={state}"
            logger.info(f"Redirect URL: {redirect_url}")

            # Redirect the user with the new authorization code
            return redirect(redirect_url, code=302)

        except jwt.DecodeError as e:
            logger.error(f"Error decoding JWT: {e}")
            return jsonify({"error": "Invalid JWT"}), 422
        except Exception as e:
            logger.error(f"Unexpected error in direct_post: {e}")
            return jsonify({"error": "Internal server error"}), 500

    else:
        logger.error("Error: id_token is missing")
        return jsonify({"error": "id_token is required"}), 422


def did_to_key(did):
    """
    Converts a DID:key into a usable PEM-encoded public key for JWT decoding.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    import base58

    # Remove the DID prefix
    assert did.startswith("did:key:z"), "Invalid DID format"
    base58_key = did[9:]  # Strip "did:key:z"

    # Decode the base58-encoded key
    try:
        multicodec_key = base58.b58decode(base58_key)
    except:
        raise ValueError("Public Key is not base58 encoded")

    # Verify and strip the multicodec prefix (P-256 -> 0x1200)
    assert multicodec_key[:2] == b"\x12\x00", "Unsupported key type"
    raw_key_material = multicodec_key[2:]

    # Reconstruct the public key
    try:
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(),  # P-256 curve
            raw_key_material,
        )
    except:
        raise ValueError("Invalid public key material")

    # Serialize the public key to PEM format
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem_key


def get_holder_key():
    return holder_public_key
