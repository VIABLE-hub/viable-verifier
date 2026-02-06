#!/usr/bin/env python3

import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from src import create_app
from src.models import TenantSettings, get_current_tenant

def update_ngrok_url(new_url):
    app = create_app()
    with app.app_context():
        tenant_id = get_current_tenant()
        tenant_settings = TenantSettings.get_or_create_default(tenant_id)
        
        # Get current network settings
        network_settings = tenant_settings.network_settings.copy() if tenant_settings.network_settings else {}
        
        # Update NGROK domain
        network_settings['ngrok_domain'] = new_url
        network_settings['use_ngrok'] = True
        
        # Save updated settings
        tenant_settings.network_settings = network_settings
        from src import db
        db.session.commit()
        
        print(f'✅ NGROK URL updated to: {new_url}')

if __name__ == "__main__":
    new_url = "8eba-2a01-599-116-5acc-2578-537b-b524-93d2.ngrok-free.app"
    update_ngrok_url(new_url) 