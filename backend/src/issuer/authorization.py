from flask import Flask, request, redirect, jsonify
from src.utils import get_current_server_url
import jwt
import uuid
import logging
from flask import current_app as app
from ..models import VC_AuthorizationCode
from .. import db

logger = logging.getLogger(__name__)


def resolve_authorization_request(request_args, private_key):
    response_type = request_args.get("response_type")
    scope = request_args.get("scope")
    state = request_args.get("state")
    client_id = request_args.get("client_id")
    authorization_details = request_args.get("authorization_details")
    redirect_uri = request_args.get("redirect_uri")
    nonce = request_args.get("nonce")
    code_challenge = request_args.get("code_challenge")
    code_challenge_method = request_args.get("code_challenge_method")
    client_metadata = request_args.get("client_metadata")
    issuer_state = request_args.get("issuer_state")

    logger.info(f"Authorization request from client_id: {client_id}")
    logger.info(f"Authorization parameters - state: {state}, nonce: {nonce}")
    logger.info(f"Code challenge: {code_challenge}, method: {code_challenge_method}")

    # Validate required parameters
    if not client_id:
        logger.error("Client id is missing")
        return "Client id is missing", 400

    if not redirect_uri:  # TODO: this is supposed to be optional???
        logger.error("Missing redirect URI")
        return "Missing redirect URI", 400

    if response_type != "code":
        logger.error(f"Unsupported response type: {response_type}")
        return "Unsupported response type", 400

    if code_challenge_method != "S256":
        logger.error(f"Invalid code challenge method: {code_challenge_method}")
        return "Invalid code challenge method", 400

    # Clean up any existing unused authorization codes for this client
    try:
        existing_entries = VC_AuthorizationCode.query.filter_by(client_id=client_id, used=False).all()
        if existing_entries:
            logger.info(f"Found {len(existing_entries)} existing unused entries for client {client_id}, cleaning up")
            for entry in existing_entries:
                db.session.delete(entry)
            db.session.commit()
            logger.info(f"Cleaned up {len(existing_entries)} old entries")
    except Exception as e:
        logger.error(f"Failed to clean up old authorization codes: {e}")
        db.session.rollback()

    # Store authorization code details in the database
    logger.info(f"Creating new authorization entry for client_id: {client_id}, issuer_state: {issuer_state}")
    
    try:
        new_auth_code = VC_AuthorizationCode(
            client_id=client_id,
            code_challenge=code_challenge,
            issuer_state=issuer_state,
            used=False
            # Note: auth_code will be set later in direct_post
        )
        db.session.add(new_auth_code)
        db.session.commit()
        logger.info(f"Successfully created authorization entry: {new_auth_code}")
    except Exception as e:
        logger.error(f"Failed to create authorization entry: {e}")
        db.session.rollback()
        return "Failed to create authorization session", 500

    # Define the response parameters
    responseType = "id_token"
    responseMode = "direct_post"
    serverUrl = get_current_server_url()
    redirectURI = f"{serverUrl}/direct_post"

    # Construct the JWT payload
    payload = {
        "iss": serverUrl,
        "aud": client_id,
        "nonce": nonce,
        "state": state,
        "client_id": client_id,
        "response_uri": client_id,
        "response_mode": responseMode,
        "response_type": responseType,
        "scope": "openid",
    }

    # JWT Header
    header = {
        "typ": "jwt",
        "alg": "ES256",
        "kid": "did:ebsi:zrZZyoQVrgwpV1QZmRUHNPz#sig-key",  # TODO: Your kid here
    }

    # Sign the JWT
    requestJar = jwt.encode(payload, private_key,
                            algorithm="ES256", headers=header)

    # Construct the redirect URL with query parameters
    redirectUrl = f"{redirect_uri}?state={state}&client_id={client_id}&redirect_uri={redirectURI}&response_type={responseType}&response_mode={responseMode}&scope=openid&nonce={nonce}&request={requestJar}"

    # Redirect to the client’s redirect URI
    return redirect(redirectUrl, code=302)
