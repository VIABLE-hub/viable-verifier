from flask import Flask, redirect, url_for, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_migrate import Migrate
import logging
import random
import os
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="urllib3")

# Create and configure the logger
log_file_path = os.path.join("..", "instance", "service.log")
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Set logging level based on environment for performance
# DEBUG in development, INFO in production (reduces log noise and improves performance)
environment = os.environ.get('ENVIRONMENT', 'development')
log_level_env = os.environ.get('LOG_LEVEL', '').upper()

if log_level_env:
    # Explicit LOG_LEVEL environment variable takes precedence
    log_level = getattr(logging, log_level_env, logging.INFO)
elif environment == 'production':
    log_level = logging.INFO  # Production: INFO level (less verbose, better performance)
else:
    log_level = logging.DEBUG  # Development: DEBUG level (more verbose for debugging)

# Set up the root logger
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(),  # Optional: To also log to the console
    ],
)

logger = logging.getLogger("LOGGER")

# Log something in the main app
logger.info("Logger initialized!")

# Create the db
db = SQLAlchemy()
migrate = Migrate()
DB_NAME = "database.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_NAME}"

# Create socketio
socketio = SocketIO()

INSTANCE_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance')


def register_blueprints(app):
    """
    Register all blueprints in one centralized location.
    
    This function provides a single source of truth for all blueprint registration,
    making it easy to see what blueprints are registered and in what order.
    
    Blueprint Categories:
    - Core: Home, Auth, Issuer, Verifier
    - Validation: VCStatus, Validate (legacy)
    - Settings: Settings UI, Settings API
    - Features: API Integration, Debug, Use Cases, Monitoring
    - Network: Network API (dynamic registration)
    
    Args:
        app: Flask application instance
    """
    # Core blueprints - Essential application functionality
    from .home import home
    from .issuer.issuer import issuer
    from .verifier.main_routes import verifier_bp as verifier
    
    app.register_blueprint(home, url_prefix='/')
    app.register_blueprint(issuer, url_prefix='/')
    app.register_blueprint(verifier, url_prefix='/verifier')
    
    # Authentication blueprints - User authentication
    from .auth import auth, vc_auth_bp
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(vc_auth_bp)  # VC-based authentication
    
    # Conditional authentication (simple session auth if enabled)
    auth_enabled = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
    if auth_enabled:
        from .simple_auth import init_auth_routes
        init_auth_routes(app)
        logger.info("🔐 Session auth enabled")
    
    # Validation blueprints - Credential validation and status
    from .validate.vcstatus import vcstatus
    from .validate.validate import validate_legacy
    
    app.register_blueprint(vcstatus, url_prefix='/vcstatus')
    app.register_blueprint(validate_legacy, url_prefix='/validate')  # Legacy route
    
    # Settings blueprints - Application configuration
    from .settings import settings, api_settings
    app.register_blueprint(settings, url_prefix='/')
    app.register_blueprint(api_settings, url_prefix='/')
    
    # Feature blueprints - Additional functionality
    from .api_integration import api_integration
    from .issuer.debug import debug as debug_bp
    from .monitoring import monitoring
    
    app.register_blueprint(api_integration, url_prefix='/')
    app.register_blueprint(debug_bp, url_prefix='/debug')
    app.register_blueprint(monitoring)
    
    # Network API - Dynamic registration (kept separate for backward compatibility)
    # from .settings.network_api import register_network_api
    # register_network_api(app)
    
    logger.info(f"Registered {len(app.blueprints)} blueprints")


# Persistent SECRET_KEY from environment or file
SECRET_KEY = os.environ.get('SECRET_KEY')

if not SECRET_KEY:
    import secrets
    secret_key_file = os.path.join(INSTANCE_PATH, '.secret_key')
    
    if os.path.exists(secret_key_file):
        # Load existing key
        try:
            with open(secret_key_file, 'r') as f:
                SECRET_KEY = f.read().strip()
            logger.info("🔐 Loaded persistent SECRET_KEY from file")
        except Exception as e:
            logger.error(f"Failed to load SECRET_KEY: {e}")
            SECRET_KEY = secrets.token_hex(32)
    else:
        # Generate new key and save
        SECRET_KEY = secrets.token_hex(32)  # 64 character hex string
        try:
            os.makedirs(INSTANCE_PATH, exist_ok=True)
            with open(secret_key_file, 'w') as f:
                f.write(SECRET_KEY)
            # Set restrictive permissions (owner read/write only)
            os.chmod(secret_key_file, 0o600)
            logger.info("🔐 Generated new persistent SECRET_KEY and saved to file")
        except Exception as e:
            logger.warning(f"Could not save SECRET_KEY to file: {e}")
else:
    logger.info("🔐 Using SECRET_KEY from environment variable")


def create_app():
    app = Flask(__name__)

    # Trust reverse-proxy headers (X-Forwarded-*) when enabled.
    # Defaults to on, can be disabled with TRUST_PROXY_HEADERS=false.
    trust_proxy_headers = os.environ.get('TRUST_PROXY_HEADERS', 'true').lower() == 'true'
    if trust_proxy_headers:
        proxy_kw = {
            'x_for': int(os.environ.get('PROXY_FIX_FOR', 1)),
            'x_proto': int(os.environ.get('PROXY_FIX_PROTO', 1)),
            'x_host': int(os.environ.get('PROXY_FIX_HOST', 1)),
            'x_port': int(os.environ.get('PROXY_FIX_PORT', 1)),
            'x_prefix': int(os.environ.get('PROXY_FIX_PREFIX', 1)),
        }
        app.wsgi_app = ProxyFix(app.wsgi_app, **proxy_kw)
        logger.info(
            "ProxyFix enabled (for=%s proto=%s host=%s port=%s prefix=%s)",
            proxy_kw['x_for'], proxy_kw['x_proto'], proxy_kw['x_host'],
            proxy_kw['x_port'], proxy_kw['x_prefix']
        )

    app.config['SECRET_KEY'] = SECRET_KEY

    # 🔧 DISABLE CACHING FOR DEVELOPMENT
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    
    # Configure URL generation - use environment variable if set
    # Don't set SERVER_NAME as it causes redirects to fail
    app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'https')
    
    # Load configuration
    from .config import Config
    app.config.from_object(Config)
    logger.info(f"Using database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
    app.config['INSTANCE_FOLDER_PATH'] = INSTANCE_PATH
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize CORS - environment-based configuration for security
    cors_origins = os.environ.get('CORS_ORIGINS', 'https://localhost:8080')
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # Production: Strict CORS with explicit origins
        allowed_origins = [origin.strip() for origin in cors_origins.split(',')]
        cors_credentials = True
        logger.info(f"CORS configured for production: {allowed_origins}")
    else:
        # Development: Allow all origins for easier testing
        allowed_origins = '*'
        cors_credentials = False
        logger.info("CORS configured for development (allow all origins)")
    
    CORS(app, resources={
        r"/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": cors_credentials
        }
    })
    
    # Initialize simple authentication (if enabled)
    auth_enabled = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
    if auth_enabled:
        from .simple_auth import init_auth_routes
        init_auth_routes(app)
        logger.info("Simple authentication enabled")
    
    # Ensure CSRF token is available for all requests
    @app.before_request
    def ensure_csrf_token():
        import secrets
        from flask import session
        
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(16)
    
    # Make csrf_token and system info accessible in templates
    @app.context_processor
    def inject_csrf_token():
        from flask import session
        from .config import Config
        
        context = {
            'csrf_token': session.get('csrf_token', ''),
            'university_name': Config.UNIVERSITY_NAME,
            'university_logo': Config.LOGO_FILENAME,
            'main_logo': Config.MAIN_LOGO_FILENAME,
            'primary_color': Config.PRIMARY_COLOR.lstrip('#'),
            # Adding other potentially used variables
        }
        
        return context

    # Optional debugging: log host-related headers to diagnose redirects/host issues
    #if os.environ.get('LOG_HOST_HEADERS', 'false').lower() == 'true':
    @app.before_request
    def log_host_headers():
        logger.info(
            "HOST DEBUG | Host=%s | XFH=%s | XFP=%s | XRI=%s | URL=%s",
            request.headers.get('Host'),
            request.headers.get('X-Forwarded-Host'),
            request.headers.get('X-Forwarded-Proto'),
            request.headers.get('X-Real-IP'),
            request.url,
        )
    
    # Explizite Route für favicon.ico, um 405-Fehler zu vermeiden
    @app.route('/favicon.ico')
    def favicon():
        return app.send_static_file('studentVC-logo-sora-cropped.png')
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize rate limiting
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per hour", "50 per minute"],
            storage_uri="memory://",  # Use Redis in production: "redis://localhost:6379"
            strategy="fixed-window",
            headers_enabled=True
        )
        app.config['RATE_LIMITER'] = limiter
        # Define rate limit decorators
        write_rate_limit = limiter.limit("10 per minute")
        read_rate_limit = limiter.limit("100 per minute")
        logger.info("✅ Rate limiting initialized")
    except Exception as e:
        logger.warning(f"⚠️ Rate limiting initialization failed: {e}")
        app.config['RATE_LIMITER'] = None
        # Define dummy decorators when rate limiting is not available
        def dummy_decorator(f):
            return f
        write_rate_limit = dummy_decorator
        read_rate_limit = dummy_decorator
    
    # Initialize system 
    logger.info("System initialized successfully")

    # Register all blueprints using centralized function
    register_blueprints(app)
    
    from .models import User

    with app.app_context():
        db.create_all()
        # addAllTrackableItems()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Match CORS configuration for security consistency
    if environment == 'production':
        socketio_cors_origins = [origin.strip() for origin in cors_origins.split(',')]
        socketio_credentials = True
        logger.info(f"Socket.IO CORS configured for production: {socketio_cors_origins}")
    else:
        socketio_cors_origins = "*"
        socketio_credentials = False
        logger.info("Socket.IO CORS configured for development (allow all)")
    
    socketio_config = {
        'cors_allowed_origins': socketio_cors_origins,
        'cors_credentials': socketio_credentials,
        'async_mode': 'threading',
        'ping_timeout': 60,           # Increased for Docker/ngrok stability
        'ping_interval': 25,
        'allow_upgrades': True,       # Allow transport upgrades
        'transports': ['polling', 'websocket'],  # Prioritize polling for Docker
        'engineio_logger': False,     # Disable for production
        'logger': False               # Disable for production
    }
    
    if os.environ.get('DOCKER_MODE') == 'true':
        socketio_config.update({
            'ping_timeout': 120,        # Longer timeout for container networking
            'ping_interval': 30,
            'transports': ['polling'],  # Polling-only for Docker reliability
            'upgrade': False            # Disable WebSocket upgrade in Docker
        })
        logger.info("Socket.IO configured for Docker mode")
    else:
        logger.info("Socket.IO configured for development mode")
    
    socketio.init_app(app, **socketio_config)

    # Create alias for /api/credentials endpoint to ensure backward compatibility
    @app.route('/api/credentials', methods=['GET'])
    def api_credentials_alias():
        from .validate.vcstatus import api_get_credentials
        return api_get_credentials()
    
    # Create alias for /api/credential/<identifier> endpoint for management operations
    @app.route('/api/credential/<string:identifier>', methods=['GET', 'PUT', 'DELETE'])
    def api_credential_manage_alias(identifier):
        from .validate.vcstatus import api_manage_credential
        return api_manage_credential(identifier)
    
    # Create alias for /api/bulk endpoint for bulk operations
    @app.route('/api/bulk', methods=['POST'])
    def api_bulk_operations_alias():
        from .validate.vcstatus import api_bulk_operations
        return api_bulk_operations()
    
    # Add specific endpoint for revoking a credential by ID
    @app.route('/api/credential/<string:identifier>/revoke', methods=['POST'])
    def api_revoke_credential(identifier):
        from .models import VC_validity, db
        
        try:
            # Validate request body
            @validate_schema(CredentialRevokeSchema)
            def validated_revoke():
                credential = VC_validity.query.filter_by(identifier=identifier).first()
                if not credential:
                    return jsonify({'error': 'Credential not found'}), 404
                
                data = request.validated_data
                reason = data.get('reason', 'Revoked via API')
                revoked_by = data.get('revoked_by', 'api')
            
                credential.revoke(reason=reason, revoked_by=revoked_by)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Credential revoked successfully',
                    'identifier': identifier,
                    'status': 'revoked',
                    'revoked_at': credential.revoked_at.isoformat() if credential.revoked_at else None
                })
            
            return validated_revoke()
        except ValidationError as e:
            return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Add specific endpoint for restoring (unrevoking) a credential by ID
    @app.route('/api/credential/<string:identifier>/restore', methods=['POST'])
    @write_rate_limit
    def api_restore_credential(identifier):
        # Validate identifier
        from .validators import IdentifierField, ValidationError
        try:
            IdentifierField()._deserialize(identifier, 'identifier', {})
        except ValidationError as e:
            return jsonify({'error': 'Invalid identifier format', 'details': str(e)}), 400
        from .models import VC_validity, db
        
        try:
            credential = VC_validity.query.filter_by(identifier=identifier).first()
            if not credential:
                return jsonify({'error': 'Credential not found'}), 404
                
            credential.restore()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Credential restored successfully',
                'identifier': identifier,
                'status': 'valid'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Add specific endpoint for deleting a credential by ID
    @app.route('/api/credential/<string:identifier>/delete', methods=['POST'])
    @write_rate_limit
    def api_delete_credential(identifier):
        # Validate identifier
        from .validators import IdentifierField, ValidationError
        try:
            IdentifierField()._deserialize(identifier, 'identifier', {})
        except ValidationError as e:
            return jsonify({'error': 'Invalid identifier format', 'details': str(e)}), 400
        from .models import VC_validity, db
        
        try:
            credential = VC_validity.query.filter_by(identifier=identifier).first()
            if not credential:
                return jsonify({'error': 'Credential not found'}), 404
                
            db.session.delete(credential)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Credential deleted successfully',
                'identifier': identifier
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Main route
    @app.route('/')
    def index():
        return redirect(url_for('issuer.index'))

    return app
