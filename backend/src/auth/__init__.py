"""
Authentication Module for StudentVC

This module provides a modular, extensible authentication system supporting:
- Traditional username/password authentication
- Verifiable Credential (VC) authentication
- Two-Factor Authentication (2FA)
- Simple password-based access control

Architecture:
- Modular design with separate modules for each auth method
- Plugin-based system for easy extension
- Shared authentication interfaces
- Comprehensive logging and error handling

Author: StudentVC Team for Educational Purposes
Version: 2.0.0
"""

from flask import Blueprint
import logging

logger = logging.getLogger(__name__)

# Create main auth blueprint (traditional auth)
auth = Blueprint('auth', __name__)

# Import VC authentication blueprint
from .vc_auth import vc_auth_bp, cleanup_expired_sessions

# Import traditional authentication routes
from .traditional_auth import *

# Export all authentication methods
__all__ = ['auth', 'vc_auth_bp', 'cleanup_expired_sessions']

logger.info("🔐 Authentication module initialized with VC support")

