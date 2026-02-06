#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# API key management routes

import os
import json
import time
import uuid
import secrets
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app, g
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

# Blueprint for API Key management
api_settings = Blueprint('api_settings', __name__)

# Mock data for now
API_KEYS = [
    {
        "id": "1234567890",
        "prefix": "sk_live_1a2b3c4d",
        "key": "sk_live_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t",  # Full key for testing
        "created_at": datetime.now().isoformat(),
        "last_used": (datetime.now() - timedelta(days=1)).isoformat(),
        "permissions": ["credentials:issue", "credentials:verify", "credentials:status", "credentials:revoke", "system:health", "admin"],
        "is_active": True,
        "name": "Test API Key"
    }
]

@api_settings.route('/api/keys/list', methods=['GET'])
def list_api_keys():
    """List all API keys"""
    try:
        # Return a copy of the API keys with full key values
        api_keys = []
        for key in API_KEYS:
            key_copy = key.copy()
            # Ensure the key property is included
            if 'key' not in key_copy or not key_copy['key']:
                key_copy['key'] = key_copy.get('prefix', '') + '...'
            api_keys.append(key_copy)
        
        return jsonify(api_keys)
    except Exception as e:
        logging.error(f"Error listing API keys: {str(e)}")
        return jsonify({"success": False, "message": "Failed to list API keys"}), 500

@api_settings.route('/api/keys/generate', methods=['POST'])
def generate_api_key():
    """Generate a new API key"""
    try:
        # Generate a random API key
        api_key = f"sk_live_{secrets.token_urlsafe(32)}"
        prefix = api_key[:12]

        # Get permissions from request
        data = request.get_json() or {}
        permissions = data.get('permissions', ["credentials:issue", "credentials:verify", "credentials:status", "credentials:revoke", "system:health"])
        name = data.get('name', "API Key")

        # Create a new API key entry
        new_key = {
            "id": str(uuid.uuid4()),
            "name": name,
            "prefix": prefix,
            "key": api_key,  # Store the full key
            "created_at": datetime.now().isoformat(),
            "permissions": permissions,
            "is_active": True
        }

        # Add to API keys list
        API_KEYS.append(new_key)

        return jsonify({
            "success": True,
            "message": "API key generated successfully",
            "key_id": new_key["id"],
            "key_prefix": prefix,
            "api_key": api_key,  # Only returned once
            "key": api_key,  # Add this for frontend compatibility
            "permissions": permissions
        })
    except Exception as e:
        logging.error(f"Error generating API key: {str(e)}")
        return jsonify({"success": False, "message": "Failed to generate API key"}), 500

@api_settings.route('/api/keys/<key_id>/revoke', methods=['POST'])
def revoke_api_key(key_id):
    """Revoke an API key"""
    try:
        # Find the API key
        key_index = -1
        for i, key in enumerate(API_KEYS):
            if key["id"] == key_id:
                key_index = i
                break

        if key_index == -1:
            return jsonify({"success": False, "message": "API key not found"}), 404

        # Remove the API key
        API_KEYS.pop(key_index)

        return jsonify({
            "success": True,
            "message": "API key revoked successfully"
        })
    except Exception as e:
        logging.error(f"Error revoking API key: {str(e)}")
        return jsonify({"success": False, "message": "Failed to revoke API key"}), 500

# Alternative endpoint for revoking API keys
@api_settings.route('/api/keys/revoke/<key_id>', methods=['POST'])
def revoke_api_key_alt(key_id):
    """Alternative endpoint for revoking an API key"""
    return revoke_api_key(key_id)

@api_settings.route('/docs', methods=['GET'])
def api_docs():
    """Redirect to API documentation (Swagger UI)"""
    # This is a placeholder. In a real implementation, you would return Swagger UI
    # or redirect to a documentation page
    return jsonify({
        "message": "API documentation will be available here",
        "endpoints": [
            {"path": "/api/health", "method": "GET", "description": "Check API health"},
            {"path": "/api/keys/list", "method": "GET", "description": "List API keys"},
            {"path": "/api/keys/generate", "method": "POST", "description": "Generate a new API key"},
            {"path": "/api/keys/{key_id}/revoke", "method": "POST", "description": "Revoke an API key"}
        ]
    }) 