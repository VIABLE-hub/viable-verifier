import json
from jwcrypto.jwk import JWK
from flask import jsonify


def pem_to_jwk(pem_key, key_type="public"):
    # Load PEM key (ensure bytes)
    if isinstance(pem_key, str):
        pem_key = pem_key.encode('utf-8')
    
    try:
        # Create JWK from PEM
        key = JWK.from_pem(pem_key)
        
        # Export as dict
        jwk_dict = key.export_public(as_dict=True)
        
        # Map 'public' to 'sig' (standard JWK 'use' values are 'sig' or 'enc')
        # The caller 'issuer.py' passes "public", which is not standard.
        if key_type == "public":
            jwk_dict['use'] = "sig"
        else:
            jwk_dict['use'] = key_type
        
        return jwk_dict

    except Exception as e:
        raise ValueError(f"Failed to convert PEM to JWK: {str(e)}")
