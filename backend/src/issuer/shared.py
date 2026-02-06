import logging
from .utils import get_placeholders
from .offer import generate_nonce

logger = logging.getLogger(__name__)

def get_credential_data(credential_data):
    logo, profile = get_placeholders()

    logger.info(f"🔍 CREDENTIAL DEBUG - Input credential_data object: {credential_data}")

    logger.info(f"🔍 CREDENTIAL DEBUG - Type of credential_data: {type(credential_data)}")
    
    actual_data = credential_data.credential_data if credential_data else None
    logger.info(f"🔍 CREDENTIAL DEBUG - Extracted credential_data: {actual_data}")
    logger.info(f"🔍 CREDENTIAL DEBUG - Type of extracted data: {type(actual_data)}")
    
    if not actual_data:
        logger.warning(f"🔍 CREDENTIAL DEBUG - No credential data found, using defaults!")
        logger.warning(f"🔍 CREDENTIAL DEBUG - This explains why user fields are missing!")
        return {
            "firstName": "Maxi" + f"{str(generate_nonce(5))}",
            "lastName": "Musterfrau" + f"{str(generate_nonce(5))}",
            "issuanceCount": "1",
            "image": profile,
            "studentId": f"{str(generate_nonce(5))}",
            "studentIdPrefix": "654321",
            "theme": {
                "name": "Technische Universität Berlin",
                "icon": logo,
                "bgColorCard": "C40D1E",
                "bgColorSectionTop": "C40D1E",
                "bgColorSectionBot": "FFFFFF",
                "fgColorTitle": "FFFFFF"
            }
        }

    logger.info(f"🔍 CREDENTIAL DEBUG - Using actual credential data with keys: {list(actual_data.keys()) if isinstance(actual_data, dict) else 'Not a dict'}")
    return actual_data
