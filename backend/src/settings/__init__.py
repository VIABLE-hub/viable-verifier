"""
Settings module for the application.
This module handles application settings, configuration, and system information.
"""

from flask import Blueprint

# Initialize the settings blueprint
settings = Blueprint('settings', __name__, url_prefix='')

# Make settings blueprint available to all submodules
import sys
sys.modules[__name__].settings = settings

# Import core functionality first
from . import core
from .core import register_routes

# Import other modules
from . import utils
from . import disclosure
from . import keys
from . import trust
from . import network
from . import health
from . import database

# Keep backward compatibility
from .api import api_settings

# Register routes from all modules
def register_all_routes():
    """Register all routes from all modules"""
    register_routes(settings)
    disclosure.register_routes(settings)
    keys.register_routes(settings)
    trust.register_routes(settings)
    network.register_routes(settings)
    health.register_routes(settings)
    database.register_routes(settings)

# Initialize routes when all modules are loaded
register_all_routes()
