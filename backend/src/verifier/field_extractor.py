"""
Field Extractor für den Verifier.

Enthält Funktionen zum Extrahieren von Feldern aus JWTs und VCs.
"""

import jwt
import json
import base64
from logging import getLogger
from urllib.parse import unquote_plus, urlparse
from .utils import multiple_url_decode
from .constants import FIELD_MAPPINGS

logger = getLogger("LOGGER")

def _get_nested_field(data_dict, field_path):
    """
    Get a nested field using dot notation (e.g., 'vc.credentialSubject.lastName')
    
    Args:
        data_dict: The dictionary to search in
        field_path: Dot-separated field path
        
    Returns:
        The field value if found, None otherwise
    """
    try:
        current = data_dict
        path_parts = field_path.split('.')
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
                
        return current
    except (KeyError, TypeError, AttributeError):
        return None

def normalize_field_name(field_name):
    """
    Normalisiert einen Feldnamen, indem camelCase zu snake_case und umgekehrt umgewandelt wird
    
    Args:
        field_name: Der zu normalisierende Feldname
        
    Returns:
        Liste mit allen möglichen Normalformen des Feldnamens
    """
    variations = [field_name]
    
    # camelCase zu snake_case
    if any(c.isupper() for c in field_name) and '_' not in field_name:
        snake_case = ''.join(['_' + c.lower() if c.isupper() else c for c in field_name]).lstrip('_')
        variations.append(snake_case)
        
    # snake_case zu camelCase
    elif '_' in field_name:
        parts = field_name.split('_')
        camel_case = parts[0] + ''.join(p.capitalize() for p in parts[1:])
        variations.append(camel_case)
        
    # Prüfe, ob es eine voreingestellte Zuordnung gibt
    if field_name in FIELD_MAPPINGS:
        mapped_name = FIELD_MAPPINGS[field_name]
        if mapped_name not in variations:
            variations.append(mapped_name)
    
    # Prüfe umgekehrte Zuordnung
    for original, mapped in FIELD_MAPPINGS.items():
        if field_name == mapped and original not in variations:
            variations.append(original)
    
    # Add user field mappings - map simple names to nested paths
    user_field_mappings = {
        'firstName': 'vc.credentialSubject.firstName',
        'lastName': 'vc.credentialSubject.lastName',
        'studentId': 'vc.credentialSubject.studentId',
        'studentIdPrefix': 'vc.credentialSubject.studentIdPrefix',
        'image': 'vc.credentialSubject.image'
    }
    
    if field_name in user_field_mappings:
        nested_path = user_field_mappings[field_name]
        if nested_path not in variations:
            variations.append(nested_path)
    
    # Reverse mapping: nested path to simple name
    for simple_name, nested_path in user_field_mappings.items():
        if field_name == nested_path and simple_name not in variations:
            variations.append(simple_name)
    
    return variations

def get_field_value(data_dict, field_name, search_depth=3):
    """
    Get field value supporting both camelCase (iOS) and snake_case (backend) naming conventions
    and checking multiple locations in the JWT structure
    """
    # Define field mappings - add working version's specific mappings
    field_mappings = {
        'total_messages': ['total_messages', 'totalMessages'],
        'bbs_dpk': ['bbs_dpk', 'bbsDPK'],
        'signed_nonce': ['signed_nonce', 'signedNonce'],
        'validity_identifier': ['validity_identifier', 'validityIdentifier']
    }
    
    # Get possible names from both new normalize function and working version mapping
    possible_names = normalize_field_name(field_name)
    if field_name in field_mappings:
        possible_names.extend(field_mappings[field_name])
    
    # Remove duplicates while preserving order
    possible_names = list(dict.fromkeys(possible_names))
    
    # Special handling for dot-separated nested paths (e.g., 'vc.credentialSubject.lastName')
    if '.' in field_name:
        try:
            result = _get_nested_field(data_dict, field_name)
            if result is not None:
                logger.debug(f"Found nested field '{field_name}' via path traversal")
                return result
        except (KeyError, TypeError):
            pass
    
    # First check directly in data_dict
    for name in possible_names:
        if name in data_dict:
            logger.debug(f"Found field '{field_name}' as '{name}' directly in data")
            return data_dict[name]
    
    # If not found and data_dict has verifiable_credential, check there
    if "verifiable_credential" in data_dict:
        vc = data_dict["verifiable_credential"]
        
        # Check at top level of verifiable_credential (important for BBS+ metadata)
        for name in possible_names:
            if name in vc:
                logger.debug(f"Found field '{field_name}' as '{name}' at top level of verifiable_credential")
                return vc[name]
        
        # Check in values of verifiable_credential
        if "values" in vc:
            values = vc["values"]
            for name in possible_names:
                if name in values:
                    logger.debug(f"Found field '{field_name}' as '{name}' in verifiable_credential.values")
                    return values[name]
    
    # If not found and data_dict has presentation_submission, check there
    if "presentation_submission" in data_dict:
        ps = data_dict["presentation_submission"]
        
        # Check at top level of presentation_submission
        for name in possible_names:
            if name in ps:
                logger.debug(f"Found field '{field_name}' as '{name}' in presentation_submission")
                return ps[name]
                
        # Check in values of presentation_submission
        if "values" in ps:
            values = ps["values"] 
            for name in possible_names:
                if name in values:
                    logger.debug(f"Found field '{field_name}' as '{name}' in presentation_submission.values")
                    return values[name]
    
    # If not found and data_dict has vp, check there
    if "vp" in data_dict:
        vp = data_dict["vp"]
        
        # Check at top level of vp
        for name in possible_names:
            if name in vp:
                logger.debug(f"Found field '{field_name}' as '{name}' in vp")
                return vp[name]
                
        # Check in verifiable_credential of vp
        if "verifiable_credential" in vp:
            vc = vp["verifiable_credential"]
            for name in possible_names:
                if name in vc:
                    logger.debug(f"Found field '{field_name}' as '{name}' in vp.verifiable_credential")
                    return vc[name]
                    
            # Check in values of verifiable_credential
            if "values" in vc:
                values = vc["values"]
                for name in possible_names:
                    if name in values:
                        logger.debug(f"Found field '{field_name}' as '{name}' in vp.verifiable_credential.values")
                        return values[name]
    
    # Tiefere Suche in verschachtelten Strukturen (optional, kann bei Bedarf aktiviert werden)
    if search_depth > 0:
        for key, value in data_dict.items():
            if isinstance(value, dict):
                result = get_field_value(value, field_name, search_depth - 1)
                if result is not None:
                    logger.debug(f"Found field '{field_name}' in nested structure under {key}")
                    return result
    
    # If not found, log available fields and return None
    if hasattr(data_dict, 'keys'):
        logger.debug(f"Field '{field_name}' not found. Available top-level fields: {list(data_dict.keys())}")
        if "verifiable_credential" in data_dict and "values" in data_dict["verifiable_credential"]:
            logger.debug(f"Available VC values fields: {list(data_dict['verifiable_credential']['values'].keys())}")
    
    return None


def extract_validity_identifier(verifiable_credential):
    """
    Extracts the validity identifier from the verifiable credential
    """
    validity_identifier = get_field_value(verifiable_credential, "validity_identifier")
    
    if validity_identifier:
        # Try to decode the validity_identifier if it appears to be URL-encoded
        if '%' in validity_identifier:
            decoded_identifier = multiple_url_decode(validity_identifier)
            logger.debug(f"Extracted validity_identifier: {decoded_identifier}")
            return decoded_identifier
        return validity_identifier
        
    logger.warning("No validity_identifier found in verifiable credential")
    return None


def extract_credential_id_from_validity_identifier(validity_identifier):
    """
    Extracts the credential ID from the validity identifier URL
    """
    if not validity_identifier:
        return None
        
    # Parse the URL to get the path
    parsed_url = urlparse(validity_identifier)
    path_parts = parsed_url.path.split('/')
    
    # The credential ID should be the last part of the URL
    if path_parts and len(path_parts) > 0:
        credential_id = path_parts[-1]
        return credential_id
        
    return None


def decode_jwt_token(jwt_token):
    """
    Decode a JWT token without verification
    """
    try:
        # Remove 'vp_token=' prefix if present (from URL parameters)
        if jwt_token.startswith("vp_token="):
            jwt_token = jwt_token[9:]
            
        # Decode without verification to extract data
        decoded_jwt = jwt.decode(jwt_token, options={"verify_signature": False})
        return decoded_jwt
    except jwt.DecodeError as e:
        logger.error(f"Error decoding JWT: {e}")
        return None


def extract_presentation_from_vp(decoded_vp):
    """
    Extracts the presentation (VP or verifiable_credential) from the decoded VP
    """
    # Normal VP/VC path
    if "vp" in decoded_vp:
        return decoded_vp["vp"]
    # iOS specific path (top-level verifiable_credential)
    elif "verifiable_credential" in decoded_vp:
        return decoded_vp
    # Direct JWT structure
    else:
        return decoded_vp
