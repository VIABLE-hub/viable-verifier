import random
import string
import segno
import io
import base64
import hashlib
from urllib.parse import unquote_plus
from logging import getLogger

logger = getLogger("LOGGER")

def multiple_url_decode(url_string, max_iterations=5):
    """
    Repeatedly URL-decode a string until it no longer changes or max_iterations is reached.
    Useful for handling double- or triple-encoded URLs from iOS wallets.
    
    Args:
        url_string: The string to decode
        max_iterations: Maximum number of decoding iterations to prevent infinite loops
    
    Returns:
        The fully decoded string
    """
    previous = url_string
    iterations = 0
    
    while iterations < max_iterations:
        decoded = unquote_plus(previous)
        if decoded == previous:  # No more changes
            break
        previous = decoded
        iterations += 1
    
    return previous


def generate_qr_code(data):
    qr = segno.make(data)
    buf = io.BytesIO()
    qr.save(buf, scale=10, kind="png")
    buf.seek(0)  # Reset the buffer pointer to the beginning
    val = buf.getvalue()
    img_data = base64.b64encode(val).decode('utf-8')
    return img_data


def randomString(stingLength=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stingLength))


def did_to_key(did):
    """
    Converts a DID:key into a usable PEM-encoded public key for JWT decoding.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    import base58
    # Remove the DID prefix
    assert did.startswith('did:key:z'), "Invalid DID format"
    base58_key = did[9:]  # Strip "did:key:z"

    # Decode the base58-encoded key
    try:
        multicodec_key = base58.b58decode(base58_key)
    except:
        raise ValueError("Public Key is not base58 encoded")

    # Verify and strip the multicodec prefix (P-256 -> 0x1200)
    assert multicodec_key[:2] == b'\x12\x00', "Unsupported key type"
    raw_key_material = multicodec_key[2:]

    # Reconstruct the public key
    try:
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(),  # P-256 curve
            raw_key_material
        )
    except:
        raise ValueError("Invalid public key material")

    # Serialize the public key to PEM format
    pem_key = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem_key


def hash_large_value(value, max_length=10000):
    """
    Erzeugt einen sicheren Hash für große Werte (wie Base64-Bilder),
    um sie in der BBS+-Verifikation zu verwenden
    
    Args:
        value: Der zu hashende Wert
        max_length: Die maximale Länge, ab der gehashed wird
        
    Returns:
        Der ursprüngliche Wert oder sein Hash, wenn er zu groß ist
    """
    if not isinstance(value, str):
        return value
        
    if len(value) <= max_length:
        return value
        
    # Für Base64-Bilder oder andere große Werte erzeugen wir einen Hash
    # Dieser bleibt für denselben Inhalt gleich, ist aber viel kürzer
    hash_obj = hashlib.sha256(value.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Wir geben die ersten 50 Zeichen des ursprünglichen Werts plus den Hash zurück
    # So können wir den Wert noch identifizieren und gleichzeitig Platz sparen
    prefix = value[:50] if len(value) > 50 else value
    logger.debug(f"Hashed large value of length {len(value)} to hash:{hash_hex}")
    return f"{prefix}...HASH:{hash_hex}"


def is_base64_image(value):
    """
    Prüft, ob ein Wert wahrscheinlich ein Base64-kodiertes Bild ist
    
    Args:
        value: Der zu prüfende Wert
        
    Returns:
        bool: True, wenn es wahrscheinlich ein Base64-kodiertes Bild ist
    """
    if not isinstance(value, str):
        return False
        
    # Typische Präfixe für Base64-kodierte Bilder
    image_prefixes = [
        "data:image/jpeg;base64,",
        "data:image/png;base64,",
        "data:image/gif;base64,",
        "data:image/webp;base64,",
        "data:image"
    ]
    
    for prefix in image_prefixes:
        if value.startswith(prefix):
            return True
    
    # Wenn kein Präfix gefunden wurde, aber der String sehr lang ist und wie Base64 aussieht
    if len(value) > 500:  # Bilder sind in der Regel länger als 500 Zeichen
        # Base64-Zeichen sind A-Z, a-z, 0-9, +, / und = (für Padding)
        base64_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
        sample_chars = set(value[:100])  # Nehme eine Stichprobe
        
        # Wenn alle Zeichen in der Stichprobe gültige Base64-Zeichen sind
        if sample_chars.issubset(base64_chars):
            return True
    
    return False


def process_oversized_fields(values, max_length=10000):
    """
    Verarbeitet große/übergroße Felder in einem Wertewörterbuch
    
    Args:
        values: Wörterbuch mit Feldwerten
        max_length: Maximale erlaubte Länge für Werte
        
    Returns:
        Verarbeitetes Wörterbuch mit sicheren Werten
    """
    if not isinstance(values, dict):
        return values
        
    processed_values = {}
    
    for key, value in values.items():
        # Prüfe auf übergroße Werte oder Base64-Bilder
        if isinstance(value, str) and (len(value) > max_length or is_base64_image(value)):
            processed_values[key] = hash_large_value(value, max_length)
            logger.debug(f"Processed oversized field '{key}' with length {len(value)}")
        else:
            processed_values[key] = value
            
    return processed_values


def get_demo_credential():
    return {
        "bbs_dpk": "Base64EncodedDPK",
        "exp": 1736460313,
        "iat": 1736456713,
        "iss": "did:key:zXwpRJo7SnJrb9KaY4oNdwcmvXodZnrMs829DYYZRkoYooovQhgqFmpgHAgpFfkPmL87rekZJbeHr9Z8n2M1vosmm2Mh",
        "jti": "urn:uuid:fb5f6ceb-f8ec-4125-9d37-55a6b1dd34d1",
        "nbf": 1736456713,
        "nonce": "rpdwshuxedrdypwcw3uy",
        "signed_nonce": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6InJwZHdzaHV4ZWRyZHlwd2N3M3V5In0.ml8yAcdyCv9asQX-Y_O2z4jjE050LsCzekEtp4Mv7zqh8kW4HadVMTdQZopIdMoCq3meh3aU8QsZj7AmvJmESw",
        "sub": "did:key:zXwpRPYqxMxCPUmtZ3cFa6nspUxToczrt84uGjGPR1Pvj9hR85UbhWVF265T9rCie6fk683TQbXSM8viKxEJzgiWoyHw",
        "total_messages": 17,
        "validity_identifier": r"https://127.0.0.1:8080/validate/isvalid/pw4uynm64ap9thhcsghkr3iyd5z435hml5yb1mzpn4gjydfpxf",
        "vc.@context.0": "https://www.w3.org/2018/credentials/v1",
        "vc.credentialSchema.id": "https://api-conformance.ebsi.eu/trusted-schemas-registry/v3/schemas/zDpWGUBenmqXzurskry9Nsk6vq2R8thh9VSeoRqguoyMD",
        "vc.credentialSchema.type": "FullJsonSchemaValidator2021",
        "vc.credentialSubject.firstName": "Max",
        "vc.credentialSubject.issuanceCount": "1",
        "vc.credentialSubject.image": "Base64hereOf35x45Image600DPI",
        "vc.credentialSubject.lastName": "Musterfrau",
        "vc.credentialSubject.studentId": "123456",
        "vc.credentialSubject.studentIdPrefix": "654321",
        "vc.credentialSubject.theme.bgColorCard": "C40D1E",
        "vc.credentialSubject.theme.bgColorSectionBot": "FFFFFF",
        "vc.credentialSubject.theme.bgColorSectionTop": "C40D1E",
        "vc.credentialSubject.theme.fgColorTitle": "FFFFFF",
        "vc.credentialSubject.theme.icon": "universityIconBase64",
        "vc.credentialSubject.theme.name": "Technische Universität Berlin",
    }