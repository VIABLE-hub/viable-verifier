#!/usr/bin/env python3
"""
Debug endpoints for JWT generation and format testing.
"""

import json
import base64
import logging
import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, Response
from uuid import uuid4

logger = logging.getLogger(__name__)

debug = Blueprint('debug', __name__)

@debug.route('/test-format', methods=['GET', 'POST'])
def test_format():
    """Debug endpoint to test credential format handling"""
    logger.info("Debug: Testing credential format handling")
    
    if request.method == 'GET':
        # Show a simple form to test different formats
        return """
        <html>
            <head><title>Test Credential Format</title></head>
            <body>
                <h1>Test Credential Format</h1>
                <form method="post">
                    <select name="format">
                        <option value="jwt_vc_json">jwt_vc_json</option>
                        <option value="jwt_vc">jwt_vc</option>
                        <option value="bbs+_vc">bbs+_vc</option>
                        <option value="ldp_vc">ldp_vc</option>
                    </select>
                    <input type="submit" value="Test Format">
                </form>
            </body>
        </html>
        """
    
    # Get the requested format
    format_value = None
    if request.is_json:
        format_value = request.json.get('format')
    elif request.form:
        format_value = request.form.get('format')
    
    logger.info(f"Debug: Testing format: {format_value}")
    
    # Create a test response
    response_data = {
        "format": "bbs+_vc",  # Always respond with bbs+_vc
        "credential": "test_jwt...",
        "signature": "test_signature...",
        "c_nonce": "test_nonce",
        "c_nonce_expires_in": 86400,
        "requested_format": format_value,
        "format_info": get_format_info(format_value),
        "note": "Server always responds with bbs+_vc regardless of request format"
    }
    
    # Validate JSON serialization
    try:
        json_response = json.dumps(response_data, ensure_ascii=False, separators=(',', ':'))
        logger.debug(f"✅ Response JSON validation passed: {len(json_response)} chars")
    except Exception as e:
        logger.error(f"❌ Response JSON validation failed: {e}")
        return jsonify({"error": "Internal JSON serialization error"}), 500
    
    # Return with explicit Content-Type for iOS compatibility
    return Response(
        json_response,
        status=200,
        mimetype='application/json',
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )

@debug.route('/test-jwt', methods=['GET', 'POST'])
def test_jwt():
    """Debug endpoint to test JWT generation and iOS compatibility"""
    logger.info("Debug: Testing JWT generation")
    
    if request.method == 'GET':
        # Show a simple form to test JWT generation
        return """
        <html>
            <head><title>Test JWT Generation</title></head>
            <body>
                <h1>Test JWT Generation</h1>
                <form method="post">
                    <label>
                        Use float timestamps:
                        <input type="checkbox" name="use_float" checked>
                    </label><br>
                    <label>
                        Add Z to dates:
                        <input type="checkbox" name="add_z" checked>
                    </label><br>
                    <input type="submit" value="Generate JWT">
                </form>
            </body>
        </html>
        """
    
    # Get the test parameters
    use_float = True  # Default to true for iOS compatibility
    add_z = True      # Default to true for iOS compatibility
    
    if request.form:
        use_float = request.form.get('use_float') == 'on'
        add_z = request.form.get('add_z') == 'on'
    elif request.is_json:
        use_float = request.json.get('use_float', True)
        add_z = request.json.get('add_z', True)
    
    logger.info(f"Debug: Generating JWT with use_float={use_float}, add_z={add_z}")
    
    # Generate a test JWT
    try:
        # Create a test payload
        current_timestamp = datetime.now(tz=timezone.utc).timestamp()
        
        # Handle timestamps based on settings
        iat = float(current_timestamp - 60) if use_float else int(current_timestamp - 60)
        exp = float(current_timestamp + 3600) if use_float else int(current_timestamp + 3600)
        nbf = float(current_timestamp) if use_float else int(current_timestamp)
        
        # Handle date strings based on settings
        issuance_date = datetime.utcnow().isoformat()
        valid_from = datetime.utcnow().isoformat()
        expiration_date = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        if add_z:
            issuance_date += "Z"
            valid_from += "Z"
            expiration_date += "Z"
        
        # Create the payload
        payload = {
            "iat": iat,
            "exp": exp,
            "nbf": nbf,
            "iss": "did:key:test_issuer",
            "sub": "did:key:test_subject",
            "jti": str(uuid4()),
            "vc": {
                "@context": ["https://www.w3.org/2018/credentials/v1"],
                "type": ["VerifiableCredential", "StudentIDCard"],
                "id": str(uuid4()),
                "issuer": "did:key:test_issuer",
                "issuanceDate": issuance_date,
                "validFrom": valid_from,
                "expirationDate": expiration_date,
                "credentialSubject": {
                    "id": "did:key:test_subject",
                    "firstName": "Test",
                    "lastName": "User",
                    "studentId": "123456"
                }
            }
        }
        
        # Additional headers
        headers = {
            "kid": "did:key:test_issuer#key-1",
            "alg": "HS256",  # Use HS256 for testing (no keys needed)
            "typ": "JWT"
        }
        
        # Generate the JWT with a dummy key for testing
        token = jwt.encode(payload, "test_secret", algorithm="HS256", headers=headers)
        
        # Analyze the JWT
        jwt_parts = token.split(".")
        header_b64 = jwt_parts[0]
        payload_b64 = jwt_parts[1]
        
        # Decode for display
        header_padding = "=" * (4 - len(header_b64) % 4)
        header_json = base64.urlsafe_b64decode(header_b64 + header_padding).decode('utf-8')
        header = json.loads(header_json)
        
        payload_padding = "=" * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + payload_padding).decode('utf-8')
        decoded_payload = json.loads(payload_json)
        
        # Create the response
        response_data = {
            "jwt": token,
            "header": header,
            "payload": decoded_payload,
            "ios_compatibility": {
                "use_float": use_float,
                "add_z": add_z,
                "timestamp_types": {
                    "iat": type(decoded_payload["iat"]).__name__,
                    "exp": type(decoded_payload["exp"]).__name__,
                    "nbf": type(decoded_payload["nbf"]).__name__
                },
                "date_formats": {
                    "issuanceDate": decoded_payload["vc"]["issuanceDate"],
                    "validFrom": decoded_payload["vc"]["validFrom"],
                    "expirationDate": decoded_payload["vc"]["expirationDate"]
                }
            },
            "recommendations": [
                "Use float timestamps for iOS Double compatibility",
                "Add Z to date strings for proper ISO format",
                "Use explicit Content-Type headers in HTTP responses"
            ]
        }
        
        # Validate JSON serialization
        json_response = json.dumps(response_data, ensure_ascii=False, separators=(',', ':'))
        logger.debug(f"✅ Response JSON validation passed: {len(json_response)} chars")
        
        # Return with explicit Content-Type for iOS compatibility
        return Response(
            json_response,
            status=200,
            mimetype='application/json',
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        
    except Exception as e:
        logger.error(f"❌ JWT generation failed: {e}")
        return jsonify({"error": f"JWT generation failed: {str(e)}"}), 500

def get_format_info(format_value):
    """Get information about the format value"""
    format_info = {
        "jwt_vc_json": "jwtVCJson enum in CredentialRequest.swift",
        "jwt_vc": "jwtVC enum in CrdentialFormat.swift",
        "bbs+_vc": "bbsVC enum in CrdentialFormat.swift",
        "ldp_vc": "ldpVC enum in CrdentialFormat.swift"
    }
    
    return format_info.get(format_value, "Unknown format") 