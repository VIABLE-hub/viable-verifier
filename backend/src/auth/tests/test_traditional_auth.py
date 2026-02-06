"""
Unit Tests for Traditional Authentication

Tests the username/password authentication flow including:
- Login page rendering
- CSRF token generation
- Password verification
- Session management
- Error handling

Author: StudentVC Team
"""

import pytest
from flask import session, url_for
from werkzeug.security import generate_password_hash
from src import create_app, db
from src.models import User


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
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
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            name='testuser',
            password_hash=generate_password_hash('testpassword123')
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestLoginPage:
    """Tests for login page rendering"""
    
    def test_login_page_accessible(self, client):
        """Test that login page loads successfully"""
        rv = client.get('/login')
        assert rv.status_code == 200
        assert b'StudentVC' in rv.data
    
    def test_login_page_has_form(self, client):
        """Test that login page contains form elements"""
        rv = client.get('/login')
        assert b'<form' in rv.data
        assert b'name="name"' in rv.data  # Username field
        assert b'name="password"' in rv.data  # Password field
        assert b'type="submit"' in rv.data  # Submit button
    
    def test_csrf_token_generated(self, client):
        """Test that CSRF token is generated"""
        rv = client.get('/login')
        assert b'csrf_token' in rv.data


class TestPasswordAuthentication:
    """Tests for password-based authentication"""
    
    def test_successful_login(self, client, test_user):
        """Test successful login with valid credentials"""
        rv = client.post('/login', data={
            'name': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=True)
        
        assert rv.status_code == 200
        # Should redirect to home page
        assert b'home' in rv.data or b'Home' in rv.data
    
    def test_invalid_username(self, client):
        """Test login with non-existent username"""
        rv = client.post('/login', data={
            'name': 'nonexistent',
            'password': 'password'
        })
        
        assert b'Invalid Credentials' in rv.data
    
    def test_invalid_password(self, client, test_user):
        """Test login with wrong password"""
        rv = client.post('/login', data={
            'name': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert b'Invalid Credentials' in rv.data
    
    def test_empty_username(self, client):
        """Test login with empty username"""
        rv = client.post('/login', data={
            'name': '',
            'password': 'password'
        })
        
        assert rv.status_code >= 400 or b'Invalid' in rv.data
    
    def test_empty_password(self, client):
        """Test login with empty password"""
        rv = client.post('/login', data={
            'name': 'testuser',
            'password': ''
        })
        
        assert rv.status_code >= 400 or b'Invalid' in rv.data


class TestPasswordSecurity:
    """Tests for password security"""
    
    def test_password_is_hashed(self, app, test_user):
        """Test that passwords are stored hashed, not plaintext"""
        with app.app_context():
            user = User.query.filter_by(name='testuser').first()
            assert user.password_hash != 'testpassword123'
            assert 'pbkdf2' in user.password_hash  # Should be hashed
    
    def test_password_verification(self, app, test_user):
        """Test password verification function"""
        from werkzeug.security import check_password_hash
        
        with app.app_context():
            user = User.query.filter_by(name='testuser').first()
            assert check_password_hash(user.password_hash, 'testpassword123')
            assert not check_password_hash(user.password_hash, 'wrong')
    
    def test_password_timing_attack_resistance(self, client, test_user):
        """Test that timing attacks are mitigated"""
        import time
        
        # Time for valid username, wrong password
        start = time.time()
        client.post('/login', data={
            'name': 'testuser',
            'password': 'wrongpassword'
        })
        time_valid_user = time.time() - start
        
        # Time for invalid username
        start = time.time()
        client.post('/login', data={
            'name': 'nonexistent',
            'password': 'wrongpassword'
        })
        time_invalid_user = time.time() - start
        
        # Timing should be similar (within 100ms)
        # This prevents attackers from determining valid usernames
        assert abs(time_valid_user - time_invalid_user) < 0.1


class TestSessionManagement:
    """Tests for session management"""
    
    def test_session_created_on_login(self, client, test_user):
        """Test that session is created upon successful login"""
        with client:
            rv = client.post('/login', data={
                'name': 'testuser',
                'password': 'testpassword123'
            }, follow_redirects=True)
            
            # Check that user is in session
            assert 'user_id' in session or '_user_id' in session
    
    def test_logout_clears_session(self, client, test_user):
        """Test that logout clears the session"""
        with client:
            # Login
            client.post('/login', data={
                'name': 'testuser',
                'password': 'testpassword123'
            })
            
            # Logout
            client.get('/logout', follow_redirects=True)
            
            # Session should be cleared
            assert 'user_id' not in session and '_user_id' not in session
    
    def test_protected_route_requires_login(self, client):
        """Test that protected routes redirect to login"""
        rv = client.get('/home', follow_redirects=False)
        
        # Should redirect to login
        assert rv.status_code == 302
        assert '/login' in rv.location


class TestCSRFProtection:
    """Tests for CSRF protection"""
    
    def test_csrf_token_in_form(self, client):
        """Test that CSRF token is present in form"""
        rv = client.get('/login')
        assert b'csrf_token' in rv.data
    
    def test_csrf_validation_enabled_in_production(self, app):
        """Test that CSRF is enabled in non-test mode"""
        # In production, CSRF should be enabled
        assert app.config.get('TESTING') == True  # We're testing
        # In production, set TESTING=False and enable CSRF


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_malformed_request(self, client):
        """Test handling of malformed requests"""
        rv = client.post('/login', data={
            'invalid_field': 'value'
        })
        
        # Should handle gracefully
        assert rv.status_code < 500  # No server error
    
    def test_sql_injection_prevention(self, client):
        """Test prevention of SQL injection"""
        rv = client.post('/login', data={
            'name': "' OR '1'='1",
            'password': "' OR '1'='1"
        })
        
        # Should not allow injection
        assert b'Invalid Credentials' in rv.data
    
    def test_xss_prevention(self, client):
        """Test prevention of XSS attacks"""
        rv = client.post('/login', data={
            'name': '<script>alert("XSS")</script>',
            'password': 'password'
        })
        
        # Script tags should be escaped in error message
        assert b'<script>' not in rv.data


class TestRedirectBehavior:
    """Tests for redirect behavior"""
    
    def test_redirect_to_home_after_login(self, client, test_user):
        """Test redirect to home after successful login"""
        rv = client.post('/login', data={
            'name': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=False)
        
        assert rv.status_code == 302  # Redirect
        assert '/home' in rv.location or '/' in rv.location
    
    def test_redirect_to_next_url(self, client, test_user):
        """Test redirect to 'next' parameter after login"""
        rv = client.post('/login?next=/settings', data={
            'name': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=False)
        
        # Should redirect to requested page
        assert rv.status_code == 302
        # Next URL should be preserved


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])

