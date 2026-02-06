script = ["dummy"]
allowed_list = script


def valid_user_rerout(input) -> bool:
    return input in allowed_list

from src.models import SystemSettings
from flask import current_app
import socket
import logging
import os

logger = logging.getLogger(__name__)

def get_server_url_no_context():
    """
    🌐 Get server URL without Flask context (for Docker environments)
    
    This function works in any environment and prioritizes external configuration.
    """
    try:
        external_url = os.environ.get('EXTERNAL_SERVER_URL')
        use_external = os.environ.get('USE_EXTERNAL_URL', 'false').lower() == 'true'
        
        if use_external and external_url:
            logger.info(f"🌍 Using EXTERNAL_SERVER_URL (no context): {external_url}")
            return external_url.rstrip('/')
        
        # Check for NGROK URL in environment
        ngrok_url = os.environ.get('NGROK_URL')
        if ngrok_url:
            logger.info(f"🌐 Using NGROK_URL from environment: {ngrok_url}")
            return ngrok_url.rstrip('/')
        
        if os.environ.get('DOCKER_MODE') == 'true':
            local_ip = get_local_ip()
            if local_ip.startswith('172.'):
                logger.warning(f"⚠️ Docker internal IP detected ({local_ip}) - mobile wallets cannot reach this!")
                logger.warning(f"⚠️ Set EXTERNAL_SERVER_URL and USE_EXTERNAL_URL=true for production")
        
        # Fallback to local IP with default port
        local_ip = get_local_ip()
        port = os.environ.get('SERVER_PORT', '8080')
        fallback_url = f"https://{local_ip}:{port}"
        
        logger.info(f"⚠️ No external/NGROK URL configured, using local IP: {fallback_url}")
        return fallback_url
        
    except Exception as e:
        logger.error(f"❌ Error getting server URL (no context): {e}")
        return "https://localhost:8080"

def get_current_server_url():
    """
    🌐 Get current server URL using unified system configuration
    
    Priority order:
    1. EXTERNAL_SERVER_URL (for production Docker deployment)
    3. Flask SERVER_URL config
    4. Local IP fallback
    
    Returns:
        str: The current server URL (either external, NGROK, or local IP)
    """
    try:
        external_url = os.environ.get('EXTERNAL_SERVER_URL')
        use_external = os.environ.get('USE_EXTERNAL_URL', 'false').lower() == 'true'
        
        if use_external and external_url:
            logger.info(f"🌍 Using EXTERNAL_SERVER_URL for production: {external_url}")
            return external_url.rstrip('/')
        
        # Try to get system information with Flask context
        try:
            logger.info("🔍 Getting server URL for system")
            
            # Get system settings from database
            system_settings = SystemSettings.get_or_create_default()
            network_settings = system_settings.network_settings or {}
            
            # Check if NGROK is enabled and URL is configured
            if network_settings.get('use_ngrok') and network_settings.get('ngrok_url'):
                ngrok_url = network_settings['ngrok_url'].strip()
                if ngrok_url:
                    logger.info(f"🌐 Using NGROK URL from system settings: {ngrok_url}")
                    return ngrok_url.rstrip('/')
            
            # Check Flask config for SERVER_URL
            server_url = current_app.config.get('SERVER_URL')
            if server_url and not server_url.startswith('https://localhost'):
                logger.info(f"🌐 Using SERVER_URL from Flask config: {server_url}")
                return server_url.rstrip('/')
                
        except RuntimeError as e:
            if "application context" in str(e):
                logger.warning(f"⚠️ No Flask context available, using environment-based URL detection")
                return get_server_url_no_context()
            else:
                raise e
        
        if os.environ.get('DOCKER_MODE') == 'true':
            local_ip = get_local_ip()
            if local_ip.startswith('172.'):
                logger.warning(f"⚠️ Docker internal IP detected ({local_ip}) - mobile wallets cannot reach this!")
                logger.warning(f"⚠️ Set EXTERNAL_SERVER_URL and USE_EXTERNAL_URL=true for production")
        
        # Fallback to local IP
        local_ip = get_local_ip()
        port = current_app.config.get('PORT', 8080)
        fallback_url = f"https://{local_ip}:{port}"
        
        logger.info(f"⚠️ No external/NGROK URL configured, using local IP: {fallback_url}")
        return fallback_url
        
    except Exception as e:
        logger.error(f"❌ Error getting server URL: {e}")
        # Fallback to environment-based detection
        return get_server_url_no_context()

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith('127.'):
            return ip
    except:
        pass
    return "127.0.0.1"
