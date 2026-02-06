import pytest
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    from src import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    import tempfile
    db_fd, db_path = tempfile.mkstemp()
    yield db_path
    os.close(db_fd)
    os.unlink(db_path)

# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "issuer: mark test as issuer functionality")
    config.addinivalue_line("markers", "verifier: mark test as verifier functionality") 
    config.addinivalue_line("markers", "settings: mark test as settings functionality")
    config.addinivalue_line("markers", "vcstatus: mark test as vc status functionality")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running") 