import json
import inspect
import base64
import hashlib
import os
import requests
import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec


def initServer():
    requests.get("https://127.0.0.1:8080/issuer", verify=False)


def pp_json(json_thing, sort=True, indents=4):
    # Try to get the variable name using inspect
    frame = inspect.currentframe().f_back
    variable_name = None

    # Check all variables in the calling frame to find the one that matches
    for name, value in frame.f_locals.items():
        if value is json_thing:
            variable_name = name
            break

    # Pretty-print the JSON
    if type(json_thing) is str:
        pretty_json = json.dumps(json.loads(
            json_thing), sort_keys=sort, indent=indents, ensure_ascii=False)
    else:
        pretty_json = json.dumps(
            json_thing, sort_keys=sort, indent=indents, ensure_ascii=False)

    # Print the variable name (if found) and the JSON
    if variable_name:
        print(f"{variable_name}:")
    else:
        print("UNKNOWN:")

    print(pretty_json)
    print()
    return None


def random_string(length=10):
    import random
    import string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def random_number(length=10):
    import random
    import string
    return ''.join(random.choices(string.digits, k=length))


def generate_pkce_challenge():
    code_verifier = base64.urlsafe_b64encode(
        os.urandom(32)).decode("utf-8").rstrip("=")
    hashed = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(
        hashed).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge


def get_keys():
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key = private_key.public_key()

    private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption())
    public_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    print(f"Generated private key: {private_key}")
    print(f"Generated public key: {public_key}")
    return private_key, public_key


def generate_holder_did(public_key_pem):
    # Decode the PEM-encoded public key to extract the raw key material

    # Load the public key from PEM
    public_key = serialization.load_pem_public_key(
        public_key_pem, backend=default_backend())

    # Get the raw public key bytes (in uncompressed form)
    raw_key_material = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )

    # Prepend the multicodec prefix for P-256 keys (0x1200)
    multicodec_prefix = b'\x12\x00'
    multicodec_key = multicodec_prefix + raw_key_material

    # Encode the multicodec key in base58
    encoded_key = base58.b58encode(multicodec_key)

    # Construct the DID key
    did = f'did:key:z{encoded_key.decode()}'
    print(f"Generated DID: {did}")
    return did


def did_to_key(did):
    """
    Converts a DID:key into a usable PEM-encoded public key for JWT decoding.
    """
    # Remove the DID prefix
    assert did.startswith('did:key:z'), "Invalid DID format"
    base58_key = did[9:]  # Strip "did:key:z"

    # Decode the base58-encoded key
    multicodec_key = base58.b58decode(base58_key)

    # Verify and strip the multicodec prefix (P-256 -> 0x1200)
    assert multicodec_key[:2] == b'\x12\x00', "Unsupported key type"
    raw_key_material = multicodec_key[2:]

    # Reconstruct the public key
    public_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(),  # P-256 curve
        raw_key_material
    )

    # Serialize the public key to PEM format
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem_key
