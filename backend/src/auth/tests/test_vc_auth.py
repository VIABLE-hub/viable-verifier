"""
Unit Tests for Verifiable Credential Authentication

Tests the VC-based authentication flow including:
- QR code generation
- VP token verification
- BBS+ signature validation
- Session management
- Real-time updates via Socket.IO

Author: StudentVC Team
"""

import pytest
import json
import uuid
from unittest.mock import Mock, patch, MagicMock
from flask import session
from src import create_app, db
from src.models import User
from src.auth.vc_auth import (
    VCSession,
    extract_user_info_from_vc,
    authenticate_with_vc,
    cleanup_expired_sessions
)


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_vp_token():
    """Sample VP token for testing"""
    return {
        "verifiable_credential": {
            "iss": "did:example:issuer",
            "sub": "did:example:holder",
            "values": {
                "studentId": "12345",
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@university.edu",
                "program": "Computer Science"
            },
            "proof": {
                "type": "BbsBlsSignature2020",
                "proofValue": "mock_proof_value"
            }
        }
    }


class TestVCSessionManagement:
    """Tests for VC session lifecycle"""
    
    def test_vc_session_creation(self):
        """Test VCSession object creation"""
        session_id = str(uuid.uuid4())
        vc_session = VCSession(session_id)
        
        assert vc_session.session_id == session_id
        assert vc_session.status == 'pending'
        assert vc_session.verified == False
        assert vc_session.user_info is None
    
    def test_vc_session_expiry(self):
        """Test that sessions expire after timeout"""
        import time
        
        vc_session = VCSession(str(uuid.uuid4()))
        
        # Fresh session should not be expired
        assert not vc_session.is_expired()
        
        # Simulate old session (5+ minutes ago)
        vc_session.created_at = time.time() - 400
        assert vc_session.is_expired()
    
    def test_vc_session_verification(self):
        """Test marking session as verified"""
        vc_session = VCSession(str(uuid.uuid4()))
        user_info = {'student_id': '12345', 'name': 'John Doe'}
        
        vc_session.mark_verified(user_info)
        
        assert vc_session.verified == True
        assert vc_session.status == 'verified'
        assert vc_session.user_info == user_info
    
    def test_vc_session_failure(self):
        """Test marking session as failed"""
        vc_session = VCSession(str(uuid.uuid4()))
        
        vc_session.mark_failed("Invalid signature")
        
        assert vc_session.status == 'failed'
        assert vc_session.error == "Invalid signature"


class TestVCLoginRequest:
    """Tests for VC login request creation"""
    
    def test_create_login_request(self, client):
        """Test POST /auth/vc-login/request endpoint"""
        rv = client.post('/auth/vc-login/request')
        
        assert rv.status_code == 200
        data = json.loads(rv.data)
        
        assert 'presentation_url' in data
        assert 'session_id' in data
        assert 'expires_in' in data
        assert data['expires_in'] == 300  # 5 minutes
    
    def test_qr_code_url_format(self, client):
        """Test that QR code URL has correct format"""
        rv = client.post('/auth/vc-login/request')
        data = json.loads(rv.data)
        
        url = data['presentation_url']
        
        # Should be an OID4VP URL
        assert 'presentation-request' in url
        assert 'response_type=vp_token' in url
        assert 'redirect_uri=' in url
        assert data['session_id'] in url
    
    def test_unique_session_ids(self, client):
        """Test that each request gets unique session ID"""
        rv1 = client.post('/auth/vc-login/request')
        rv2 = client.post('/auth/vc-login/request')
        
        data1 = json.loads(rv1.data)
        data2 = json.loads(rv2.data)
        
        assert data1['session_id'] != data2['session_id']


class TestVCCallback:
    """Tests for VC callback handling"""
    
    @patch('src.auth.vc_auth.decode_jwt_token')
    @patch('src.auth.vc_auth.safe_verify_presentation')
    def test_successful_vc_callback(self, mock_verify, mock_decode, 
                                   client, sample_vp_token):
        """Test successful VC presentation verification"""
        # Setup mocks
        mock_decode.return_value = sample_vp_token
        mock_verify.return_value = (True, {'status': 'valid'})
        
        # Create session first
        rv = client.post('/auth/vc-login/request')
        session_data = json.loads(rv.data)
        session_id = session_data['session_id']
        
        # Send VP callback
        rv = client.post(f'/auth/vc-login/callback?session_id={session_id}',
                        data={'vp_token': 'mock_vp_token'})
        
        assert rv.status_code == 200
        data = json.loads(rv.data)
        assert data['valid'] == 1
        assert 'redirect_url' in data
    
    @patch('src.auth.vc_auth.decode_jwt_token')
    @patch('src.auth.vc_auth.safe_verify_presentation')
    def test_invalid_vp_token(self, mock_verify, mock_decode, client):
        """Test handling of invalid VP token"""
        # Mock invalid token
        mock_decode.return_value = None
        
        # Create session
        rv = client.post('/auth/vc-login/request')
        session_data = json.loads(rv.data)
        session_id = session_data['session_id']
        
        # Send invalid VP
        rv = client.post(f'/auth/vc-login/callback?session_id={session_id}',
                        data={'vp_token': 'invalid_token'})
        
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert 'error' in data
    
    def test_missing_vp_token(self, client):
        """Test handling of missing VP token"""
        # Create session
        rv = client.post('/auth/vc-login/request')
        session_data = json.loads(rv.data)
        session_id = session_data['session_id']
        
        # Send request without VP token
        rv = client.post(f'/auth/vc-login/callback?session_id={session_id}')
        
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert 'error' in data
        assert 'vp_token' in data['error'].lower()
    
    def test_expired_session(self, client):
        """Test handling of expired session"""
        import time
        from src.auth.vc_auth import vc_sessions, VCSession
        
        # Create expired session manually
        session_id = str(uuid.uuid4())
        vc_session = VCSession(session_id)
        vc_session.created_at = time.time() - 400  # 6+ minutes ago
        vc_sessions[session_id] = vc_session
        
        # Try to use expired session
        rv = client.post(f'/auth/vc-login/callback?session_id={session_id}',
                        data={'vp_token': 'mock_token'})
        
        assert rv.status_code == 400
        data = json.loads(rv.data)
        assert 'expired' in data['error'].lower()


class TestUserExtraction:
    """Tests for extracting user info from VC"""
    
    def test_extract_user_info(self, sample_vp_token):
        """Test extraction of user information from VC"""
        user_info = extract_user_info_from_vc(sample_vp_token)
        
        assert user_info['student_id'] == '12345'
        assert user_info['first_name'] == 'John'
        assert user_info['last_name'] == 'Doe'
        assert user_info['name'] == 'John Doe'
        assert user_info['email'] == 'john.doe@university.edu'
        assert user_info['program'] == 'Computer Science'
    
    def test_extract_with_missing_fields(self):
        """Test extraction with missing optional fields"""
        minimal_vp = {
            "verifiable_credential": {
                "values": {
                    "studentId": "54321"
                }
            }
        }
        
        user_info = extract_user_info_from_vc(minimal_vp)
        
        assert user_info['student_id'] == '54321'
        assert user_info['name'] == '54321'  # Fallback to student ID


class TestUserAuthentication:
    """Tests for user creation and authentication"""
    
    def test_create_new_user_from_vc(self, app):
        """Test creating new user from VC"""
        with app.app_context():
            user_info = {
                'student_id': '12345',
                'name': 'John Doe',
                'email': 'john@example.com'
            }
            
            user = authenticate_with_vc(user_info)
            
            assert user is not None
            assert user.name == '12345'  # Username is student ID
            assert User.query.filter_by(name='12345').first() is not None
    
    def test_authenticate_existing_user(self, app):
        """Test authenticating existing user with VC"""
        with app.app_context():
            # Create user first
            from werkzeug.security import generate_password_hash
            existing_user = User(
                name='12345',
                password_hash=generate_password_hash('dummy')
            )
            db.session.add(existing_user)
            db.session.commit()
            
            user_info = {
                'student_id': '12345',
                'name': 'John Doe'
            }
            
            user = authenticate_with_vc(user_info)
            
            assert user is not None
            assert user.id == existing_user.id
    
    def test_user_password_not_usable(self, app):
        """Test that VC-created users have random password"""
        with app.app_context():
            user_info = {
                'student_id': '99999',
                'name': 'VC User'
            }
            
            user = authenticate_with_vc(user_info)
            
            # Password should be hashed random value
            assert user.password_hash is not None
            assert len(user.password_hash) > 20  # Hash should be long


class TestSessionCleanup:
    """Tests for expired session cleanup"""
    
    def test_cleanup_expired_sessions(self):
        """Test cleanup of expired sessions"""
        import time
        from src.auth.vc_auth import vc_sessions
        
        # Create mix of expired and active sessions
        active_id = str(uuid.uuid4())
        expired_id = str(uuid.uuid4())
        
        vc_sessions[active_id] = VCSession(active_id)
        
        expired_session = VCSession(expired_id)
        expired_session.created_at = time.time() - 400
        vc_sessions[expired_id] = expired_session
        
        # Run cleanup
        cleanup_expired_sessions()
        
        # Active session should remain
        assert active_id in vc_sessions
        # Expired session should be removed
        assert expired_id not in vc_sessions


class TestSocketIOIntegration:
    """Tests for Socket.IO real-time updates"""
    
    @patch('src.auth.vc_auth.socketio')
    @patch('src.auth.vc_auth.decode_jwt_token')
    @patch('src.auth.vc_auth.safe_verify_presentation')
    def test_socketio_events_emitted(self, mock_verify, mock_decode, 
                                    mock_socketio, client, sample_vp_token):
        """Test that Socket.IO events are emitted during verification"""
        # Setup mocks
        mock_decode.return_value = sample_vp_token
        mock_verify.return_value = (True, {'status': 'valid'})
        
        # Create session
        rv = client.post('/auth/vc-login/request')
        session_data = json.loads(rv.data)
        session_id = session_data['session_id']
        
        # Send VP callback
        client.post(f'/auth/vc-login/callback?session_id={session_id}',
                   data={'vp_token': 'mock_vp_token'})
        
        # Check that events were emitted
        assert mock_socketio.emit.called
        
        # Check event types
        calls = [call[0] for call in mock_socketio.emit.call_args_list]
        event_names = [call[0] for call in calls]
        
        # Should emit events for: received, verified
        assert any('received' in str(call) for call in calls)
        assert any('verified' in str(call) for call in calls)


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

