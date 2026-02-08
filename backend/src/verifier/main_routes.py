"""
Main Verifier Routes - Combines all route modules.

Primary entry point for the verifier with UI and core functionality.
"""

from flask import Blueprint, render_template, request, jsonify
from src.utils import get_current_server_url
from logging import getLogger
from datetime import datetime
import uuid
import json

from ..models import VerificationSession, db
from .utils import generate_qr_code, get_demo_credential, randomString
from .presentation_routes import presentation_bp
from .verification_routes import verification_bp
from .debug_routes import debug_bp

logger = getLogger("LOGGER")

# Main verifier blueprint that combines all functionality
verifier_bp = Blueprint("verifier", __name__)

# Register sub-blueprints
verifier_bp.register_blueprint(presentation_bp)
verifier_bp.register_blueprint(verification_bp)
verifier_bp.register_blueprint(debug_bp)


@verifier_bp.route("/create-session", methods=["POST"])
def create_session():
    try:
        data = request.get_json()
        selected_fields = data.get("fields", [])
        
        # Generate session ID and nonce
        session_id = str(uuid.uuid4())
        nonce = randomString(10)
        
        # Create session
        session = VerificationSession(
            id=session_id,
            nonce=nonce,
            requested_fields=selected_fields,
            status="created"
        )
        db.session.add(session)
        db.session.commit()
        
        # Construct URLs
        # 🚀 PRODUCTION-READY: Use configurable URLs
        external_server_url = get_current_server_url()
        
        # This URL is what the wallet fetches to get the Presentation Definition
        # We point it to existing request.uri route which we will modify to handle session IDs correctly
        request_uri = f"{external_server_url}/request.uri/{session_id}"
        
        # This is the OpenID4VP URL encoded in the QR code
        presentation_request_url = (
            f"openid4vp://?request_uri={request_uri}"
        )
        
        # Generate QR Code
        img = generate_qr_code(presentation_request_url)
        
        return jsonify({
            "session_id": session_id,
            "qr_code_data": img,
            "presentation_request_url": presentation_request_url,
            "request_uri": request_uri
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500



@verifier_bp.before_request
def log_request_info():
    logger.info("--- VERIFIER REQUEST ---")
    logger.info(f"Endpoint: {request.endpoint}")
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Args: {request.args.to_dict()}")
    if request.method in ["POST", "PUT", "PATCH"]:
        logger.info(f"Form data: {request.form.to_dict()}")
        # Safely access JSON data only if content type is JSON
        try:
            if request.is_json:
                logger.info(f"JSON data: {request.get_json()}")
            else:
                logger.info("JSON data: Not a JSON request")
        except Exception as e:
            logger.info(f"JSON data: Error accessing JSON - {e}")
        logger.info(f"Content-Type: {request.content_type}")
    logger.info("--- END REQUEST ---")


@verifier_bp.route("/", methods=["GET"])
def index():
    # 🚀 PRODUCTION-READY: Use configurable URLs for QR code and Socket.IO
    external_server_url = get_current_server_url()  # External URL for QR code

    # Socket.IO URL: Use environment variable or same as external for production
    import os

    socket_server_url = os.environ.get("SOCKET_IO_URL", external_server_url)

    # NEW: Create a unique session for this visitor
    session_id = str(uuid.uuid4())
    nonce = randomString(10)
    
    # Store session
    session = VerificationSession(
        id=session_id,
        nonce=nonce,
        requested_fields=[], # Default fields will be handled by request handler
        status="created"
    )
    db.session.add(session)
    db.session.commit()

    # Construct OID4VP URL with Session ID
    request_uri = f"{external_server_url}/request.uri/{session_id}"
    presentation_request_url = (
        f"openid4vp://?request_uri={request_uri}"
    )
    img = generate_qr_code(presentation_request_url)

    return render_template(
        "verifier.html",
        img_data=img,
        presentation_request_url=presentation_request_url,  # For display below QR
        session_id=session_id, # PASS SESSION ID TO TEMPLATE
        server_url=external_server_url,  # For QR code generation
        socket_url=socket_server_url,  # For Socket.IO connection
        demo_credential=get_demo_credential(),
        year=datetime.now().year,
    )
