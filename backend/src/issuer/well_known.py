from flask import jsonify
from src.utils import get_current_server_url


def openid_credential_issuer():
    # 🩺 HERZCHIRURG FIX: Use get_current_server_url() for ngrok compatibility
    server_url = get_current_server_url()
    metadata = {
        "credential_issuer": server_url,
        "authorization_server": server_url,
        "authorization_servers": [server_url],  # Add authorization_servers array for iOS compatibility
        "credential_endpoint": f"{server_url}/credential",
        "token_endpoint": f"{server_url}/token",  # Add explicit token endpoint
        "jwks_uri": f"{server_url}/jwks",
        "credential_response_encryption": {
            "alg_values_supported": ["ECDH-ES"],
            "enc_values_supported": ["A128GCM"],
            "encryption_required": False,
        },
        "display": [
            {
                "name": "Technical University of Berlin",
                "locale": "en-US",
                "logo": {
                    "url": "https://logowik.com/content/uploads/images/technischen-universitat-berlin1469.jpg",
                },
            }
        ],
        "credentials_supported": [
            {
                "format": "jwt_vc",
                "types": [
                    "VerifiableCredential",
                    "VerifiableAttestation",
                    "UniversityDegreeCredential",
                    "CTWalletSamePreAuthorisedInTime",
                    "CTWalletSameAuthorisedInTime",
                ],
                "cryptographic_binding_methods_supported": [
                    "DID"
                ],
                "cryptographic_suites_supported": [
                    "ES256",
                    "ES256K"
                ],
                "display": [
                    {
                        "name": "EU Diploma",
                        "locale": "en-US",
                        "description": "This is the official EBSI VC Diploma",
                        "background_color": "#3B6F6D",
                        "text_color": "#FFFFFF",
                        "logo": {
                            "uri": "https://dutchblockchaincoalition.org/assets/images/icons/Logo-DBC.png",
                            "alt_text": "An orange block shape, with the text Dutch Blockchain Coalition next to it, portraying the logo of the Dutch Blockchain Coalition."
                        },
                        "background_image": {
                            "uri": "https://i.ibb.co/CHqjxrJ/dbc-card-hig-res.png",
                            "alt_text": "Connected open cubes in blue with one orange cube as a background of the card"
                        }
                    }
                ],
                "trust_framework": {
                    "name": "ebsi",
                    "type": "Accreditation",
                    "uri": "TIR link towards accreditation"
                },
                "credentialSubject": {
                    "givenNames": {
                        "display": [
                            {"name": "First Name", "locale": "en-US"},
                            {"name": "Vorname", "locale": "de-DE"},
                        ]
                    },
                    "familyName": {
                        "display": [
                            {"name": "Family Name", "locale": "en-US"},
                            {"name": "Nachname", "locale": "de-DE"},
                        ]
                    },
                    "dateOfBirth": {
                        "display": [
                            {"name": "Birth Date", "locale": "en-US"},
                            {"name": "GeburtsDatum", "locale": "de-DE"},
                        ]
                    },
                    "gpa": {
                        "display": [
                            {"name": "GPA", "locale": "en-us"},
                            {"name": "Note", "locale": "de-DE"},
                        ]
                    },
                }
            }
        ],
    }

    return jsonify(metadata), 200


def openid_configuration():
    # 🩺 HERZCHIRURG FIX: Use get_current_server_url() for ngrok compatibility  
    server_url = get_current_server_url()
    config = {
        "issuer": server_url,
        "authorization_endpoint": f"{server_url}/authorize",
        "token_endpoint": f"{server_url}/token",
        "jwks_uri": f"{server_url}/jwks",
        "scopes_supported": ["openid"],
        "response_types_supported": ["code", "vp_token", "id_token"],
        "response_modes_supported": ["query"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["ES256"],
        "request_object_signing_alg_values_supported": ["ES256"],
        "request_parameter_supported": True,
        "request_uri_parameter_supported": True,
        "token_endpoint_auth_methods_supported": ["private_key_jwt"],
        "vp_formats_supported": {
            "jwt_vp": {
                "alg_values_supported": ["ES256"]
            },
            "jwt_vc": {
                "alg_values_supported": ["ES256"]
            }
        },
        "subject_syntax_types_supported": ["did:key", "did:ebsi"],
        "subject_trust_frameworks_supported": ["ebsi"],
        "id_token_types_supported": [
            "subject_signed_id_token",
            "attester_signed_id_token"
        ]
    }

    return jsonify(config), 200
