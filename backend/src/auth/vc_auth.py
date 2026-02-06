"""
Verifiable Credential Authentication Module

This module provides VC-based authentication for StudentVC platform.
Students can login using their verifiable credentials instead of passwords.

Architecture:
- Modular design for easy testing and maintenance
- Socket.IO integration for real-time verification
- Session-based authentication flow
- BBS+ signature verification

Author: StudentVC Team
Version: 1.0.0
"""

import uuid
import time
import logging
from typing import Dict, Optional, Tuple
from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user
from ..models import User, db
from ..verifier.field_extractor import decode_jwt_token, extract_presentation_from_vp
from ..verifier.integration import safe_verify_presentation
from ..verifier.settings_integration import get_presentation_definition
from .. import socketio

logger = logging.getLogger(__name__)

# Blueprint for VC authentication routes
vc_auth_bp = Blueprint('vc_auth', __name__, url_prefix='/auth/vc-login')

# In-memory storage for VC login sessions (use Redis in production)
vc_sessions = {}

# Session cleanup (remove sessions older than 5 minutes)
VC_SESSION_TIMEOUT = 300  # 5 minutes


class VCAuthenticationError(Exception):
    """Custom exception for VC authentication errors"""
    pass


class VCSession:
    """
    Represents a VC authentication session
    
    Each session tracks:
    - Unique session ID
    - Creation timestamp
    - Verification status
    - Extracted user info from VC
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.status = 'pending'
        self.user_info = None
        self.verified = False
        
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return (time.time() - self.created_at) > VC_SESSION_TIMEOUT
        
    def mark_verified(self, user_info: Dict):
        """Mark session as verified with user information"""
        self.verified = True
        self.status = 'verified'
        self.user_info = user_info
        
    def mark_failed(self, error: str):
        """Mark session as failed"""
        self.status = 'failed'
        self.error = error


@vc_auth_bp.route('/request', methods=['POST'])
def create_vc_login_request():
    """
    Create a VC presentation request for login
    
    Returns:
        JSON with presentation URL and session ID
        
    Example Response:
        {
            "presentation_url": "openid-vc://?request_uri=...",
            "session_id": "uuid-string",
            "expires_in": 300
        }
    """
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create VC session
        vc_session = VCSession(session_id)
        vc_sessions[session_id] = vc_session
        
        # Get server URL
        from ..utils import get_current_server_url
        server_url = get_current_server_url()
        
        # Build presentation request URL
        presentation_url = f"{server_url}/verifier/presentation-request"
        
        # Add session ID to callback
        callback_url = f"{server_url}/auth/vc-login/callback?session_id={session_id}"
        
        # Create OID4VP request
        request_params = {
            "response_type": "vp_token",
            "response_mode": "direct_post",
            "client_id": server_url,
            "redirect_uri": callback_url,
            "state": session_id,
            "nonce": str(uuid.uuid4()),
            "presentation_definition": get_presentation_definition()
        }
        
        # Build full URL
        from urllib.parse import urlencode
        full_url = f"{presentation_url}?{urlencode(request_params)}"
        
        logger.info(f"✅ Created VC login session: {session_id}")
        
        return jsonify({
            "presentation_url": full_url,
            "session_id": session_id,
            "expires_in": VC_SESSION_TIMEOUT
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating VC login request: {e}")
        return jsonify({"error": str(e)}), 500


@vc_auth_bp.route('/callback', methods=['POST'])
def handle_vc_callback():
    """
    Handle the VC presentation callback
    
    This endpoint receives the verifiable presentation from the wallet
    and verifies it to authenticate the user.
    
    Flow:
    1. Extract vp_token and session_id
    2. Decode and verify the VP
    3. Extract user information
    4. Create or authenticate user
    5. Emit success via Socket.IO
    """
    try:
        # Extract parameters
        vp_token = request.form.get('vp_token') or request.args.get('vp_token')
        session_id = request.args.get('session_id') or request.form.get('state')
        
        if not vp_token:
            raise VCAuthenticationError("No vp_token provided")
            
        if not session_id or session_id not in vc_sessions:
            raise VCAuthenticationError("Invalid or expired session")
        
        vc_session = vc_sessions[session_id]
        
        if vc_session.is_expired():
            del vc_sessions[session_id]
            raise VCAuthenticationError("Session expired")
        
        # Emit received status
        socketio.emit(f'vc_login_{session_id}', {
            'status': 'received',
            'message': 'Credential received'
        })
        
        # Decode the VP token
        decoded_vp = decode_jwt_token(vp_token)
        if not decoded_vp:
            raise VCAuthenticationError("Failed to decode VP token")
        
        # Extract presentation
        presentation = extract_presentation_from_vp(decoded_vp)
        
        # Verify the presentation
        presentation_def = get_presentation_definition()
        valid, verification_details = safe_verify_presentation(decoded_vp, presentation_def)
        
        if not valid:
            error_msg = verification_details.get('error', 'Verification failed')
            vc_session.mark_failed(error_msg)
            
            # Emit error status
            socketio.emit(f'vc_login_{session_id}', {
                'status': 'error',
                'message': error_msg
            })
            
            return jsonify({"error": error_msg, "valid": 0}), 400
        
        # Extract user information from VC
        user_info = extract_user_info_from_vc(decoded_vp)
        
        # Authenticate or create user
        user = authenticate_with_vc(user_info)
        
        if not user:
            raise VCAuthenticationError("Failed to authenticate user")
        
        # Mark session as verified
        vc_session.mark_verified(user_info)
        
        # Create Flask-Login session
        login_user(user, remember=True)
        
        logger.info(f"✅ VC authentication successful for user: {user.name}")
        
        # Emit success status
        socketio.emit(f'vc_login_{session_id}', {
            'status': 'verified',
            'message': 'Login successful',
            'redirect_url': url_for('home.index')
        })
        
        # Clean up session
        del vc_sessions[session_id]
        
        return jsonify({
            "valid": 1,
            "message": "Authentication successful",
            "redirect_url": url_for('home.index')
        })
        
    except VCAuthenticationError as e:
        logger.error(f"❌ VC authentication error: {e}")
        return jsonify({"error": str(e), "valid": 0}), 400
        
    except Exception as e:
        logger.error(f"❌ Unexpected error in VC callback: {e}")
        return jsonify({"error": "Internal server error", "valid": 0}), 500


def extract_user_info_from_vc(decoded_vp: Dict) -> Dict:
    """
    Extract user information from verified credential
    
    Args:
        decoded_vp: Decoded verifiable presentation
        
    Returns:
        Dictionary with user information:
        {
            'student_id': '12345',
            'name': 'John Doe',
            'email': 'john@example.com',
            'program': 'Computer Science'
        }
    """
    try:
        # Get the credential from VP
        vc = decoded_vp.get('verifiable_credential', {})
        if not vc and 'vp' in decoded_vp:
            vcs = decoded_vp['vp'].get('verifiableCredential', [])
            if vcs:
                vc = vcs[0]
        
        # Extract values
        values = vc.get('values', {})
        
        # Map fields to user info
        user_info = {
            'student_id': values.get('studentId') or values.get('student_id'),
            'first_name': values.get('firstName') or values.get('first_name'),
            'last_name': values.get('lastName') or values.get('last_name'),
            'email': values.get('email'),
            'program': values.get('program'),
            'issuer': vc.get('issuer', {}).get('id') or vc.get('iss')
        }
        
        # Create full name
        if user_info['first_name'] and user_info['last_name']:
            user_info['name'] = f"{user_info['first_name']} {user_info['last_name']}"
        else:
            user_info['name'] = user_info['student_id'] or 'VC User'
        
        logger.info(f"📋 Extracted user info: {user_info['name']} ({user_info['student_id']})")
        
        return user_info
        
    except Exception as e:
        logger.error(f"❌ Error extracting user info: {e}")
        raise VCAuthenticationError(f"Failed to extract user info: {e}")


def authenticate_with_vc(user_info: Dict) -> Optional[User]:
    """
    Authenticate or create user based on VC information
    
    Strategy:
    1. Look for existing user by student_id
    2. If not found, create new user
    3. Update user information if changed
    
    Args:
        user_info: Dictionary with user information from VC
        
    Returns:
        User object or None
    """
    try:
        student_id = user_info.get('student_id')
        if not student_id:
            raise VCAuthenticationError("No student ID in credential")
        
        # Look for existing user
        user = User.query.filter_by(name=student_id).first()
        
        if not user:
            # Create new user
            logger.info(f"👤 Creating new user from VC: {student_id}")
            
            # Generate a secure random password (user won't use it)
            import secrets
            from werkzeug.security import generate_password_hash
            random_password = secrets.token_urlsafe(32)
            
            user = User(
                name=student_id,
                password_hash=generate_password_hash(random_password)
            )
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"✅ Created new user: {user.name}")
        else:
            logger.info(f"✅ Found existing user: {user.name}")
        
        return user
        
    except Exception as e:
        logger.error(f"❌ Error authenticating with VC: {e}")
        db.session.rollback()
        return None


@vc_auth_bp.route('/status/<session_id>', methods=['GET'])
def check_session_status(session_id: str):
    """
    Check the status of a VC authentication session
    
    Useful for polling-based clients that don't use Socket.IO
    """
    if session_id not in vc_sessions:
        return jsonify({"error": "Session not found"}), 404
    
    vc_session = vc_sessions[session_id]
    
    if vc_session.is_expired():
        del vc_sessions[session_id]
        return jsonify({"status": "expired"}), 410
    
    return jsonify({
        "status": vc_session.status,
        "verified": vc_session.verified,
        "created_at": vc_session.created_at
    })


def cleanup_expired_sessions():
    """
    Clean up expired VC sessions
    
    Should be called periodically (e.g., every minute)
    """
    expired_sessions = []
    
    for session_id, vc_session in vc_sessions.items():
        if vc_session.is_expired():
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del vc_sessions[session_id]
        logger.debug(f"🧹 Cleaned up expired VC session: {session_id}")
    
    if expired_sessions:
        logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired VC sessions")

