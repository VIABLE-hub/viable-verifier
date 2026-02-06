"""
Main Verifier Routes - Combines all route modules.

Primary entry point for the verifier with UI and core functionality.
"""

from flask import Blueprint, render_template, request
from src.utils import get_current_server_url
from logging import getLogger
from datetime import datetime
from flask_login import login_required

from .utils import generate_qr_code, get_demo_credential
from .settings_integration import (
    get_current_selective_disclosure_settings,
    update_selective_disclosure_settings,
)
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


@verifier_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # 🚀 PRODUCTION-READY: Use configurable URLs for QR code and Socket.IO
    external_server_url = get_current_server_url()  # External URL for QR code

    # Socket.IO URL: Use environment variable or same as external for production
    import os

    socket_server_url = os.environ.get("SOCKET_IO_URL", external_server_url)

    # Construct OID4VP URL
    presentation_request_url = (
        f"openid4vp://?request_uri={external_server_url}/verifier/presentation-request"
    )
    img = generate_qr_code(presentation_request_url)

    # TODO: why load mandatory fields, then save in database then load again
    # Get current settings dynamically
    current_mandatory_fields = get_current_selective_disclosure_settings()

    if request.method == "GET":
        return render_template(
            "verifier.html",
            img_data=img,
            presentation_request_url=presentation_request_url,  # For display below QR
            server_url=external_server_url,  # For QR code generation
            socket_url=socket_server_url,  # For Socket.IO connection
            mandatory_fields=current_mandatory_fields,
            demo_credential=get_demo_credential(),
            year=datetime.now().year,
        )

    # update the mandatory fields - filter out form control fields
    from .constants import ALL_SELECTABLE_FIELDS

    selected_fields = [
        field for field in request.form.keys() if field in ALL_SELECTABLE_FIELDS
    ]

    logger.info(f"Form keys received: {list(request.form.keys())}")
    logger.info(f"Filtered selectable fields: {selected_fields}")

    # Update settings in database (even if empty - that means no user fields required)
    update_selective_disclosure_settings(selected_fields)

    # Get updated settings after the change
    updated_mandatory_fields = get_current_selective_disclosure_settings()

    return render_template(
        "verifier.html",
        img_data=img,
        presentation_request_url=presentation_request_url,  # For display below QR
        server_url=external_server_url,  # For QR code generation
        socket_url=socket_server_url,  # For Socket.IO connection
        mandatory_fields=updated_mandatory_fields,
        demo_credential=get_demo_credential(),
        year=datetime.now().year,
    )


@verifier_bp.route("/settings", methods=["GET", "POST"])
def verifier_settings():
    current_mandatory_fields = get_current_selective_disclosure_settings()
    return render_template(
        "verifier_settings.html",
        mandatory_fields=current_mandatory_fields,
        demo_credential=get_demo_credential(),
        year=datetime.now().year,
    )
