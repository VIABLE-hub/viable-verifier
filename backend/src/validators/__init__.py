"""
Input Validation Framework
Centralized validation for all API endpoints

This module provides:
- Schema-based validation using Marshmallow
- Common validators (URLs, identifiers)
- Validation decorator for easy route protection
- Consistent error responses

Usage:
    from src.validators import validate_schema, NetworkConfigSchema
    
    @app.route('/api/settings/network', methods=['POST'])
    @validate_schema(NetworkConfigSchema)
    def update_network():
        data = request.validated_data  # Already validated
        # ... safe to use
"""

from marshmallow import Schema, fields, validate, ValidationError
import re
from functools import wraps
from flask import request, jsonify

# Common validators


class URLField(fields.String):
    """Validates URLs"""
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if not value:
            return value  # Allow None/empty for optional fields
        
        # URL pattern: http:// or https://, domain or IP, optional port
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)?$', re.IGNORECASE)
        
        if not url_pattern.match(value):
            raise ValidationError(f"Invalid URL format: {value}. Must be http:// or https:// URL")
        return value


class IdentifierField(fields.String):
    """Validates credential identifiers"""
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        # Identifier should be alphanumeric with dashes/underscores, 1-255 chars
        if not re.match(r'^[a-zA-Z0-9_-]{1,255}$', value):
            raise ValidationError(f"Invalid identifier format: {value}. Must be 1-255 alphanumeric characters with dashes/underscores")
        return value


# API Schemas
class NetworkConfigSchema(Schema):
    """Schema for network configuration updates"""
    ngrok_url = URLField(required=False, allow_none=True)
    local_url = URLField(required=False, allow_none=True)


class CredentialIdentifierSchema(Schema):
    """Schema for credential identifier validation"""
    identifier = IdentifierField(required=True)


class BulkOperationSchema(Schema):
    """Schema for bulk credential operations"""
    operation = fields.String(
        required=True,
        validate=validate.OneOf(['revoke', 'restore', 'delete'])
    )
    identifiers = fields.List(
        IdentifierField(),
        required=True,
        validate=validate.Length(min=1, max=100)  # Max 100 at once
    )
    reason = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))


class CredentialRevokeSchema(Schema):
    """Schema for credential revocation"""
    reason = fields.String(required=False, allow_none=True, validate=validate.Length(max=500))
    revoked_by = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))


class SelectiveDisclosureSchema(Schema):
    """Schema for selective disclosure settings"""
    fields = fields.List(
        fields.String(validate=validate.Length(min=1, max=100)),
        required=False,
        allow_none=True,
        validate=validate.Length(max=50)  # Max 50 fields
    )


# Validation decorator
def validate_schema(schema_class):
    """
    Decorator to validate request data against schema.
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_schema(MySchema)
        def my_endpoint():
            data = request.validated_data  # Already validated
            # ... use data safely
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            schema = schema_class()
            
            try:
                # Validate JSON body
                if request.is_json:
                    data = schema.load(request.get_json() or {})
                    request.validated_data = data
                # Validate form data
                elif request.form:
                    data = schema.load(request.form.to_dict())
                    request.validated_data = data
                # Validate URL params
                elif request.args:
                    data = schema.load(request.args.to_dict())
                    request.validated_data = data
                else:
                    return jsonify({
                        'error': 'Validation failed',
                        'message': 'No data provided',
                        'details': {}
                    }), 400
                
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation failed',
                    'message': 'Invalid input data',
                    'details': err.messages
                }), 400
            except Exception as e:
                return jsonify({
                    'error': 'Validation error',
                    'message': str(e),
                    'details': {}
                }), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator


# Utility function for manual validation
def validate_data(data, schema_class):
    """
    Manually validate data against a schema.
    
    Returns:
        tuple: (is_valid, validated_data_or_errors)
    """
    try:
        schema = schema_class()
        validated = schema.load(data)
        return True, validated
    except ValidationError as err:
        return False, err.messages

