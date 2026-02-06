# Health module for settings
from . import routes
from . import system
from . import services

# Function to register all health routes
def register_routes(blueprint):
    """Register all health routes with the provided blueprint"""
    routes.register_routes(blueprint)
    system.register_routes(blueprint)
    services.register_routes(blueprint) 