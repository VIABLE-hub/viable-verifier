from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required
from logging import getLogger
from .key_generator import generate_did, generate_kid, load_or_generate_bbs_keys, load_or_generate_keys
from .offer import get_offer_url
from .token import authenticate_token, verify_token, verify_and_generate_token
from .credential import generate_credential, resolve_credential_offer
from .well_known import openid_credential_issuer, openid_configuration
from .jwks import pem_to_jwk
from .authorization import resolve_authorization_request
from .direct_post import resolve_direct_post
from .qr_codes import generate_qr_code
from .utils import preprocess_image, get_placeholders, preprocess_theme_icon
from .csv_import import parse_csv_students, get_csv_template
import os
import base64
from datetime import datetime

# Diese Variablen werden bei Bedarf später aktualisiert
placeholder_logo, placeholder_profile = None, None

issuer = Blueprint('issuer', __name__)
logger = getLogger("LOGGER")


# Add request logging middleware for issuer routes
@issuer.before_request
def log_request_info():
    logger.info('--- ISSUER REQUEST ---')
    logger.info(f'Endpoint: {request.endpoint}')
    logger.info(f'Method: {request.method}')
    logger.info(f'URL: {request.url}')
    logger.info(f'Headers: {dict(request.headers)}')
    logger.info(f'Args: {request.args.to_dict()}')
    if request.method in ['POST', 'PUT', 'PATCH']:
        logger.info(f'Form data: {request.form.to_dict()}')
        # Safely access JSON data only if content type is JSON
        try:
            if request.is_json:
                logger.info(f'JSON data: {request.get_json()}')
            else:
                logger.info('JSON data: Not a JSON request')
        except Exception as e:
            logger.info(f'JSON data: Error accessing JSON - {e}')
        logger.info(f'Content-Type: {request.content_type}')
    logger.info('--- END REQUEST ---')


private_key = None
public_key = None
jwks = None
issuer_did = None
issuer_kid = None
bbs_dpk = None
bbs_secret = None


@issuer.route('/issuer', methods=['GET', 'POST'])
@login_required
def index():
    initialize_keys()
    if request.method == "GET":
        # Pre-populate form with config defaults for GET requests
        try:
            vc_template = current_app.config.get('CREDENTIAL_TEMPLATE', {})
            branding = vc_template.get("credentialSubject", {}).get("credentialBranding", {})

            # Get values
            system_logo = branding.get("vcLogo", 'studentVC-logo-sora-cropped-darkmode.png')
            branding_bg_card = branding.get("bgColorCard", "").lstrip('#') or 'c50e1f'
            branding_bg_top = branding.get("bgColorSectionTop", "").lstrip('#') or 'c50e1f'
            branding_bg_bot = branding.get("bgColorSectionBot", "").lstrip('#') or ''
            branding_fg_title = branding.get("fgColorTitle", "").lstrip('#') or ''

            logger.info(f"🎓 GET REQUEST - Using system config")

            # Load specific logo as base64 if it exists
            system_logo_base64 = None
            system_logo_url = None
            try:
                # Assuming logos are in static/img/
                if system_logo and system_logo != 'studentVC-logo-sora-cropped-darkmode.png':
                    system_logo_path = os.path.join(current_app.static_folder, 'img', system_logo)
                    if os.path.exists(system_logo_path):
                        with open(system_logo_path, 'rb') as f:
                            system_logo_base64 = base64.b64encode(f.read()).decode('utf-8')
                        system_logo_url = url_for('static', filename=f'img/{system_logo}')
                    else:
                        logger.warning(f"🎓 LOGO WARNING - Logo not found at: {system_logo_path}")
            except Exception as e:
                logger.error(f"🎓 LOGO ERROR - Failed to load logo: {e}")

            # Create initial form data
            from ..config import Config
            form_data = {
                'firstName': '',
                'lastName': '',
                'studentId': '',
                'studentIdPrefix': '',
                'theme_name': Config.UNIVERSITY_NAME,
                'theme_bgColorCard': branding_bg_card,
                'theme_bgColorSectionTop': branding_bg_top,
                'theme_bgColorSectionBot': branding_bg_bot,
                'theme_fgColorTitle': branding_fg_title,
                'default_logo': system_logo,
                'profile_image': None,
                'theme_icon': system_logo_base64 if system_logo_base64 else None,  # Use base64 content or None
                'theme_icon_url': system_logo_url  # URL for direct access
            }

            return render_template("issuer.html", img_data=None, form_data=form_data)

        except Exception as e:
            logger.info(f"🎓 GET REQUEST ERROR - Using defaults: {e}")
            # Fallback to original behavior
            return render_template("issuer.html", img_data=None)

    # Process the form data
    credential_data = request.form.to_dict()
    logger.info(f"🩺 Received form data: {credential_data}")
    logger.info(f"🩺 Received files: {request.files}")

    # 🔧 DEBUG: Log the color values specifically
    logger.info(f"🎨 COLOR DEBUG - Form colors received:")
    logger.info(f"🎨   bgColorCard: {credential_data.get('theme[bgColorCard]')}")
    logger.info(f"🎨   bgColorSectionTop: {credential_data.get('theme[bgColorSectionTop]')}")
    logger.info(f"🎨   bgColorSectionBot: {credential_data.get('theme[bgColorSectionBot]')}")
    logger.info(f"🎨   fgColorTitle: {credential_data.get('theme[fgColorTitle]')}")

    # Get system VC branding configuration
    try:
        vc_template = current_app.config.get('CREDENTIAL_TEMPLATE', {})
        branding = vc_template.get("credentialSubject", {}).get("credentialBranding", {})

        # Use system logo, fallback to form data, then to default
        system_logo = branding.get("vcLogo")
        default_logo = credential_data.get('default_logo', system_logo or 'studentVC-logo-sora-cropped-darkmode.png')

        logger.info(f"🎓 VC BRANDING - Using config")
        logger.info(f"🎓 VC BRANDING - Logo: {system_logo}")
        logger.info(f"🎓 VC BRANDING - Final logo: {default_logo}")
    except Exception as e:
        # Fallback to original logic if system fails
        default_logo = credential_data.get('default_logo', 'studentVC-logo-sora-cropped-darkmode.png')
        logger.info(f"🎓 ERROR - Fallback to default logo: {default_logo}, Error: {e}")

    default_profile = 'student.png'  # Immer student.png als Standard

    # Lade die Platzhalter mit den angegebenen Standardwerten
    placeholder_logo, placeholder_profile = get_placeholders(default_logo, default_profile)
    logger.info(f"🩺 Using default logo: {default_logo}, default profile: {default_profile}")

    profile_image = request.files.get('image')
    if profile_image:
        logger.info(f"🩺 Received profile image from upload")
        img = preprocess_image(profile_image, (400, 400), keep_aspect_ratio=True)
        credential_data['image'] = img
    else:
        # 🩺 HERZCHIRURG FIX: Nur Standard verwenden wenn KEIN Bild vorhanden
        # Prüfe ob bereits ein Bild im State ist, sonst nutze Standard
        if not credential_data.get('image'):
            credential_data['image'] = placeholder_profile
            logger.info(f"🩺 No image provided - using default profile image")

    theme_icon_image = request.files.get('theme[icon]')
    if theme_icon_image:
        logger.info(f"🩺 Received theme icon image from upload")
        img = preprocess_theme_icon(
            theme_icon_image, (400, 300), keep_aspect_ratio=True)
        credential_data['theme[icon]'] = img
    else:
        # 🩺 HERZCHIRURG FIX: Nur Standard verwenden wenn KEIN Logo vorhanden
        if not credential_data.get('theme[icon]'):
            credential_data['theme[icon]'] = placeholder_logo
            logger.info(f"🩺 No theme icon provided - using default logo: {default_logo}")

    # Get config colors for theme defaults
    try:
        vc_template = current_app.config.get('CREDENTIAL_TEMPLATE', {})
        branding = vc_template.get("credentialSubject", {}).get("credentialBranding", {})

        # Extract system colors (remove # prefix for the form)
        branding_bg_card = branding.get("bgColorCard", "").lstrip('#')
        branding_bg_top = branding.get("bgColorSectionTop", "").lstrip('#')
        branding_bg_bot = branding.get("bgColorSectionBot", "").lstrip('#')
        branding_fg_title = branding.get("fgColorTitle", "").lstrip('#')

        logger.info(f"🎨 COLORS - Card: {branding_bg_card}, Top: {branding_bg_top}")

        # Use system colors as defaults
        default_bg_card = branding_bg_card or 'c50e1f'
        default_bg_top = branding_bg_top or 'c50e1f'
        default_bg_bot = branding_bg_bot or ''
        default_fg_title = branding_fg_title or ''

    except Exception as e:
        # Fallback defaults if system fails
        logger.info(f"🎨 COLORS ERROR - Using defaults: {e}")
        default_bg_card = 'c50e1f'
        default_bg_top = 'c50e1f'
        default_bg_bot = ''
        default_fg_title = ''

    # Manually group the theme-related data
    theme_data = {
        "name": credential_data.get('theme[name]'),
        "icon": credential_data.get('theme[icon]'),
        "bgColorCard": credential_data.get('theme[bgColorCard]') or default_bg_card,
        "bgColorSectionTop": credential_data.get('theme[bgColorSectionTop]') or default_bg_top,
        "bgColorSectionBot": credential_data.get('theme[bgColorSectionBot]') or default_bg_bot,
        "fgColorTitle": credential_data.get('theme[fgColorTitle]') or default_fg_title
    }

    # Create the full credential object
    full_credential_data = {
        "firstName": credential_data.get('firstName'),
        "lastName": credential_data.get('lastName'),
        "issuanceCount": "1",
        "image": credential_data.get('image'),
        "studentId": credential_data.get('studentId'),
        "studentIdPrefix": credential_data.get('studentIdPrefix'),
        "theme": theme_data
    }

    # Now you can use full_credential_data as needed
    link = get_offer_url(full_credential_data)
    logger.info(f"Generated QR code link: {link}")
    img = generate_qr_code(link)

    # 🩺 HERZCHIRURG FIX: Erweitere form_data um Bild-Informationen mit Branding
    form_data = {
        'firstName': credential_data.get('firstName', ''),
        'lastName': credential_data.get('lastName', ''),
        'studentId': credential_data.get('studentId', ''),
        'studentIdPrefix': credential_data.get('studentIdPrefix', ''),
        'theme_name': credential_data.get('theme[name]', ''),
        'theme_bgColorCard': credential_data.get('theme[bgColorCard]', default_bg_card),
        'theme_bgColorSectionTop': credential_data.get('theme[bgColorSectionTop]', default_bg_top),
        'theme_bgColorSectionBot': credential_data.get('theme[bgColorSectionBot]', default_bg_bot),
        'theme_fgColorTitle': credential_data.get('theme[fgColorTitle]', default_fg_title),
        'default_logo': default_logo,
        'profile_image': credential_data.get('image'),  # Übertrage auch das aktuelle Bild
        'theme_icon': credential_data.get('theme[icon]'),  # Übertrage auch das aktuelle Logo
        'theme_icon_url': credential_data.get('theme_icon_url')  # Übertrage auch die URL für direkten Zugriff
    }

    # Load config logo as base64 for form display if no custom icon was uploaded
    if not credential_data.get('theme[icon]'):
        try:
            vc_template = current_app.config.get('CREDENTIAL_TEMPLATE', {})
            branding = vc_template.get("credentialSubject", {}).get("credentialBranding", {})
            system_logo = branding.get("vcLogo")

            if system_logo and system_logo != 'studentVC-logo-sora-cropped-darkmode.png':
                # Assuming static/img/
                logo_path = os.path.join(current_app.static_folder, 'img', system_logo)
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        system_logo_base64 = base64.b64encode(f.read()).decode('utf-8')
                        form_data['theme_icon'] = system_logo_base64
                        form_data['theme_icon_url'] = url_for('static', filename=f'img/{system_logo}')
                        logger.info(f"🎓 POST - Loaded logo as base64: {len(system_logo_base64)} chars")
        except Exception as e:
            logger.error(f"🎓 POST LOGO ERROR - Failed to load logo: {e}")

    logger.info(f"🩺 Sending form data back to template: {list(form_data.keys())}")
    logger.info(f"🩺 QR code generated, credential link: {link}")
    logger.info(f"🩺 HERZCHIRURG DEBUG - COMPLETE FORM_DATA: {form_data}")

    # 🔧 DEBUG: Log the final color values being sent to template
    logger.info(f"🎨 COLOR DEBUG - Final colors in form_data:")
    logger.info(f"🎨   theme_bgColorCard: {form_data.get('theme_bgColorCard')}")
    logger.info(f"🎨   theme_bgColorSectionTop: {form_data.get('theme_bgColorSectionTop')}")
    logger.info(f"🎨   theme_bgColorSectionBot: {form_data.get('theme_bgColorSectionBot')}")
    logger.info(f"🎨   theme_fgColorTitle: {form_data.get('theme_fgColorTitle')}")

    # 🩺 HERZCHIRURG FIX: Gib sowohl den QR-Code als auch die Formulardaten zurück
    return render_template("issuer.html", img_data=img, form_data=form_data, credential_link=link)


@issuer.route("/offer", methods=["POST"])
def offer():
    initialize_keys()
    # Generate the credential offer URI
    logger.info("Received request to generate credential offer")

    # check if the request has a json
    # if request.json:
    #     logger.info(f"Received credential data: {request.json}")
    #     return redirect(get_offer_url(request.json))
    credential_offer_uri = get_offer_url(None)
    logger.info(f"Generated credential offer URI: {credential_offer_uri}")
    return redirect(credential_offer_uri)


def initialize_keys():
    global private_key, public_key, jwks, issuer_did, issuer_kid, bbs_dpk, bbs_secret
    if not private_key or not public_key or not bbs_dpk or not bbs_secret:
        # Load keys
        private_key, public_key = load_or_generate_keys()
        bbs_secret, bbs_dpk = load_or_generate_bbs_keys()

        # Generate DID and KID
        issuer_did = generate_did(public_key)
        issuer_kid = generate_kid(issuer_did)

    if not jwks:
        jwks = pem_to_jwk(public_key, "public")
    # return jsonify({"credential_offer": credential_offer_uri}), 200


@issuer.route("/verifyAccessToken", methods=["POST"])
def verify_access_token():
    logger.info(f"Received token verification request:")
    data = request.get_json()
    logger.info(f"Received token verification request: {data}")
    return verify_token(data, public_key)


@issuer.route("/credential", methods=["POST"])
@authenticate_token
def create_credential():
    logger.info("Received request to create a credential")
    auth_header = request.headers.get("Authorization")

    # Check for format in request body
    try:
        data = request.get_json(silent=True) or {}
        credential_format = data.get("format", "bbs")
    except Exception:
        credential_format = "bbs"

    logger.info(f"Received credential request with auth header: {auth_header} and format: {credential_format}")
    return generate_credential(auth_header, public_key, private_key, issuer_did, issuer_kid, bbs_dpk, bbs_secret,
                               format=credential_format)


@issuer.route("/.well-known/openid-credential-issuer", methods=["GET"])
def get_credential_issuer_metadata():
    logger.info("Received request for credential issuer metadata")
    return openid_credential_issuer()


@issuer.route("/.well-known/openid-configuration", methods=["GET"])
def get_openid_configuration():
    logger.info("Received request for openid configuration")
    return openid_configuration()


@issuer.route("/credential-offer/<Uid>", methods=["GET"])
def get_credential_offer(Uid):
    logger.info(f"Received request for credential offer with Uid: {Uid}")
    return resolve_credential_offer(Uid)


@issuer.route("/jwks", methods=["GET"])
def get_jwks():
    initialize_keys()
    logger.info("Received request for JWKS")
    keys = [
        {**jwks, "kid": "did:ebsi:zrZZyoQVrgwpV1QZmRUHNPz#sig-key", "use": "sig"},
        {**jwks, "kid": "did:ebsi:zrZZyoQVrgwpV1QZmRUHNPz#authentication-key",
         "use": "keyAgreement"}
    ]

    return jsonify({"keys": keys}), 200


@issuer.route("/authorize", methods=["GET"])
def authorize():
    logger.info("Received authorization request")
    return resolve_authorization_request(request.args, private_key)


@issuer.route("/direct_post", methods=["POST"])
def direct_post():
    logger.info("Received direct post request")
    state = request.args.get("state")
    id_jwt = request.args.get("id_token")
    
    logger.info(
        f"Received direct post request with state: {state} and id_token: {id_jwt}")
    return resolve_direct_post(state, id_jwt)


@issuer.route('/token', methods=['POST'])
def token():
    logger.info("Received token request")
    initialize_keys()  # Ensure keys are initialized
    # Fix: Use request.form for POST data instead of request.args
    request_data = request.form.to_dict() if request.form else request.json or {}
    logger.info(f"Received token request: {request_data}")
    logger.info(f"Request headers: {dict(request.headers)}")
    logger.info(f"Request content type: {request.content_type}")
    return verify_and_generate_token(request_data, private_key)


# =============================================================================
# DEBUG ENDPOINTS - Add these to help diagnose authentication issues
# =============================================================================

@issuer.route('/debug/tokens', methods=['GET'])
def debug_tokens():
    """Debug endpoint to check stored tokens in database"""
    logger.info("Debug: Checking stored tokens")
    try:
        from ..models import VC_Token, VC_AuthorizationCode, VC_Offer

        # Get all tokens
        tokens = VC_Token.query.all()
        auth_codes = VC_AuthorizationCode.query.all()
        offers = VC_Offer.query.all()

        debug_info = {
            "tokens_count": len(tokens),
            "auth_codes_count": len(auth_codes),
            "offers_count": len(offers),
            "tokens": [
                {
                    "id": token.id,
                    "token_preview": token.token[:20] + "..." if token.token else None,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "created_at": getattr(token, 'created_at', 'N/A')
                } for token in tokens
            ],
            "auth_codes": [
                {
                    "id": code.id,
                    "code_preview": code.code[:10] + "..." if code.code else None,
                    "created_at": getattr(code, 'created_at', 'N/A')
                } for code in auth_codes
            ],
            "offers": [
                {
                    "id": offer.id,
                    "uid": offer.uid,
                    "created_at": getattr(offer, 'created_at', 'N/A')
                } for offer in offers
            ]
        }

        logger.info(f"Debug tokens result: {debug_info}")
        return jsonify(debug_info), 200

    except Exception as e:
        logger.error(f"Debug tokens error: {e}")
        return jsonify({"error": f"Debug failed: {e}"}), 500


@issuer.route('/debug/test-token', methods=['POST'])
def debug_test_token():
    """Debug endpoint to test token generation and verification"""
    logger.info("Debug: Testing token generation and verification")
    try:
        initialize_keys()

        # Generate a test token
        test_client_id = "debug-client"
        test_credential_id = "debug-credential"

        from .token import generate_access_token
        test_token = generate_access_token(test_client_id, test_credential_id, private_key)

        # Try to verify the token
        verification_result = verify_token({"token": test_token}, public_key)

        debug_info = {
            "test_token_generated": test_token[:50] + "..." if test_token else None,
            "verification_status": verification_result[1],
            "verification_response": verification_result[0].get_json() if hasattr(verification_result[0],
                                                                                  'get_json') else str(
                verification_result[0])
        }

        logger.info(f"Debug test token result: {debug_info}")
        return jsonify(debug_info), 200

    except Exception as e:
        logger.error(f"Debug test token error: {e}")
        return jsonify({"error": f"Debug test token failed: {e}"}), 500


@issuer.route('/debug/oauth-flow', methods=['GET'])
def debug_oauth_flow():
    """Debug endpoint to show OAuth2 flow status"""
    logger.info("Debug: Checking OAuth2 flow status")
    try:
        initialize_keys()

        flow_info = {
            "server_endpoints": {
                "credential_offer": "/credential-offer/<uid>",
                "authorize": "/authorize",
                "token": "/token",
                "credential": "/credential",
                "verify_token": "/verifyAccessToken"
            },
            "keys_initialized": {
                "private_key": bool(private_key),
                "public_key": bool(public_key),
                "bbs_dpk": bool(bbs_dpk),
                "bbs_secret": bool(bbs_secret),
                "issuer_did": issuer_did,
                "issuer_kid": issuer_kid
            },
            "well_known_endpoints": {
                "openid_credential_issuer": "/.well-known/openid-credential-issuer",
                "openid_configuration": "/.well-known/openid-configuration",
                "jwks": "/jwks"
            }
        }

        logger.info(f"Debug OAuth flow result: {flow_info}")
        return jsonify(flow_info), 200

    except Exception as e:
        logger.error(f"Debug OAuth flow error: {e}")
        return jsonify({"error": f"Debug OAuth flow failed: {e}"}), 500

    # =============================================================================


# CSV IMPORT & STUDENT MANAGEMENT ENDPOINTS
# =============================================================================

@issuer.route('/issuer/csv-template', methods=['GET'])
@login_required
def download_csv_template():
    """Download a CSV template for student data import"""
    logger.info("CSV: Template download requested")
    from flask import Response

    template = get_csv_template()

    return Response(
        template,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=student_template.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )


@issuer.route('/issuer/import-csv', methods=['POST'])
@login_required
def import_csv():
    """Import students from CSV file and store in session"""
    logger.info("CSV: Import request received")

    if 'csvFile' not in request.files:
        return jsonify({'success': False, 'error': 'No CSV file provided'}), 400

    csv_file = request.files['csvFile']

    if csv_file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not csv_file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'error': 'File must be a CSV file'}), 400

    try:
        file_content = csv_file.read()
        result = parse_csv_students(file_content)

        if result['valid_rows'] == 0:
            return jsonify({
                'success': False,
                'error': 'No valid student records found in CSV',
                'errors': result['errors']
            }), 400

        # Store students in session
        from flask import session
        session['imported_students'] = result['students']

        logger.info(f"CSV: Imported {result['valid_rows']} students successfully")

        return jsonify({
            'success': True,
            'message': f"Successfully imported {result['valid_rows']} students",
            'total_rows': result['total_rows'],
            'valid_rows': result['valid_rows'],
            'errors': result['errors'],
            'students': result['students']
        }), 200

    except Exception as e:
        logger.error(f"CSV: Import error: {e}")
        return jsonify({'success': False, 'error': f'Import failed: {str(e)}'}), 500


@issuer.route('/issuer/students', methods=['GET'])
@login_required
def get_students():
    """Get all imported students"""
    from flask import session
    students = session.get('imported_students', [])

    return jsonify({
        'success': True,
        'students': students,
        'total': len(students),
        'stats': {
            'pending': len([s for s in students if s.get('status') == 'pending']),
            'qr_generated': len([s for s in students if s.get('status') == 'qr_generated']),
            'issued': len([s for s in students if s.get('status') == 'issued'])
        }
    }), 200


@issuer.route('/issuer/students/<student_id>/generate-qr', methods=['POST'])
@login_required
def generate_student_qr(student_id):
    """Generate QR code for a specific student"""
    initialize_keys()
    from flask import session

    students = session.get('imported_students', [])
    student = next((s for s in students if s.get('id') == student_id), None)

    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    try:
        # Get default images
        placeholder_logo, placeholder_profile = get_placeholders(
            'studentVC-logo-sora-cropped-darkmode.png',
            'student.png'
        )

        # Get tenant theme
        theme_data = {
            "name": "StudentVC",
            "icon": system_logo,
            "bgColorCard": "c50e1f",
            "bgColorSectionTop": "c50e1f",
            "bgColorSectionBot": "FFFFFF",
            "fgColorTitle": "FFFFFF"
        }

        try:
            from ..tenants.registry import get_current_tenant_config
            tenant_config = get_current_tenant_config()
            if tenant_config:
                vc_template = tenant_config.get_credential_template()
                branding = vc_template.get("credentialSubject", {}).get("credentialBranding", {})
                theme_data["name"] = tenant_config.name
                theme_data["bgColorCard"] = branding.get("bgColorCard", "").lstrip('#') or 'c50e1f'
                theme_data["bgColorSectionTop"] = branding.get("bgColorSectionTop", "").lstrip('#') or 'c50e1f'
        except Exception as e:
            logger.warning(f"Could not get tenant theme: {e}")

        # Create credential data
        full_credential_data = {
            "firstName": student.get('firstName'),
            "lastName": student.get('lastName'),
            "issuanceCount": "1",
            "image": placeholder_profile,
            "studentId": student.get('studentId'),
            "studentIdPrefix": student.get('studentIdPrefix', ''),
            "theme": theme_data
        }

        # Generate QR code
        link = get_offer_url(full_credential_data)
        img = generate_qr_code(link)

        # Update student status
        student['status'] = 'qr_generated'
        student['viewed'] = False
        student['qrCode'] = img
        student['credentialLink'] = link
        student['qrGeneratedAt'] = datetime.now().isoformat()

        # Save back to session
        session['imported_students'] = students
        session.modified = True

        logger.info(f"CSV: Generated QR for student {student.get('firstName')} {student.get('lastName')}")

        return jsonify({
            'success': True,
            'student': student,
            'qrCode': img,
            'credentialLink': link
        }), 200

    except Exception as e:
        logger.error(f"CSV: QR generation error for {student_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@issuer.route('/issuer/students/generate-bulk', methods=['POST'])
@login_required
def generate_bulk_qr():
    """Generate QR codes for multiple selected students"""
    initialize_keys()
    from flask import session

    data = request.get_json()
    student_ids = data.get('studentIds', [])

    if not student_ids:
        return jsonify({'success': False, 'error': 'No students selected'}), 400

    students = session.get('imported_students', [])

    # Get defaults
    placeholder_logo, placeholder_profile = get_placeholders(
        'studentVC-logo-sora-cropped-darkmode.png',
        'student.png'
    )

    theme_data = {
        "name": "StudentVC",
        "icon": placeholder_logo,
        "bgColorCard": "c50e1f",
        "bgColorSectionTop": "c50e1f",
        "bgColorSectionBot": "FFFFFF",
        "fgColorTitle": "FFFFFF"
    }

    results = []
    errors = []

    for student_id in student_ids:
        student = next((s for s in students if s.get('id') == student_id), None)

        if not student:
            errors.append({'id': student_id, 'error': 'Student not found'})
            continue

        try:
            full_credential_data = {
                "firstName": student.get('firstName'),
                "lastName": student.get('lastName'),
                "issuanceCount": "1",
                "image": placeholder_profile,
                "studentId": student.get('studentId'),
                "studentIdPrefix": student.get('studentIdPrefix', ''),
                "theme": theme_data
            }

            link = get_offer_url(full_credential_data)
            img = generate_qr_code(link)

            student['status'] = 'qr_generated'
            student['viewed'] = False
            student['qrCode'] = img
            student['credentialLink'] = link

            results.append({
                'id': student_id,
                'name': f"{student.get('firstName')} {student.get('lastName')}",
                'qrCode': img,
                'credentialLink': link
            })

        except Exception as e:
            errors.append({'id': student_id, 'error': str(e)})

    session['imported_students'] = students
    session.modified = True

    logger.info(f"CSV: Bulk generated {len(results)} QR codes, {len(errors)} errors")

    return jsonify({
        'success': True,
        'generated': len(results),
        'failed': len(errors),
        'results': results,
        'errors': errors
    }), 200


@issuer.route('/issuer/students/clear', methods=['POST'])
@login_required
def clear_students():
    """Clear all imported students"""
    from flask import session
    session.pop('imported_students', None)
    logger.info("CSV: Cleared all imported students")

    return jsonify({'success': True, 'message': 'All students cleared'}), 200

@issuer.route('/issuer/students/<student_id>/mark-viewed', methods=['POST'])
@login_required
def mark_student_viewed(student_id):
    """Mark a student's QR code as having been viewed"""
    from flask import session
    students = session.get('imported_students', [])
    student = next((s for s in students if s.get('id') == student_id), None)

    if student:
        student['viewed'] = True
        session['imported_students'] = students
        session.modified = True
        return jsonify({'success': True}), 200
    return jsonify({'success': False, 'error': 'Student not found'}), 404
