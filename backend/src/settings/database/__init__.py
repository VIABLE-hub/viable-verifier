# Database module initialization
from . import backup
from . import export
from . import info
from . import routes
from . import utils

# Function to register all database routes
def register_routes(blueprint):
    """Register all database routes with the provided blueprint"""
    routes.register_routes(blueprint)
    backup.register_routes(blueprint)
    export.register_routes(blueprint)
    info.register_routes(blueprint) 