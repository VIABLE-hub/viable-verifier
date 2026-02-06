# Network module initialization
from . import config
from . import diagnostics
from . import ngrok
from . import utils

# Import routes module
from . import routes

# Function to register all network routes
def register_routes(blueprint):
    """Register all network routes with the provided blueprint"""
    routes.register_routes(blueprint)
    config.register_routes(blueprint)
    diagnostics.register_routes(blueprint)
    ngrok.register_routes(blueprint)

# Network module for settings
from . import routes, utils 