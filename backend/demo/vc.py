from cfg import host, client_id, private_key, code_verifier, code_challenge, holder_did
from utils import pp_json, did_to_key
import requests
import jwt
from urllib.parse import urlparse, parse_qs
import copy


def generate_jwt_proof():
    payload = {
        "iss": holder_did,
        "sub": client_id,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256")
    return token


def get_vc(token):
    # irrelevant
    payload = {
        "format": "bbs+_vc",  # iOS CredentialFormat.bbsVC expects exactly "bbs+_vc"
        "credential_definition": {
            "type": [
                "VerifiableCredential",
                "VerifiablePortableDocumentA1"
            ]
        },
        "proof": {
            "proof_type": "jwt",
            "jwt": "eyJraWQiOiJkaWQ6ZX..zM"
        }
    }

    response = requests.post(
        f"{host}/credential",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json=payload,
        verify=False
    )

    vc_res = response.json()
    raw_vc = vc_res["credential"]
    vc_res["credential"] = jwt.decode(
        vc_res["credential"], options={"verify_signature": False})

    issuer_did = vc_res["credential"]["iss"]
    issuer_key = did_to_key(issuer_did)
    vc_res["credential"] = jwt.decode(
        raw_vc, issuer_key, algorithms=["ES256"], verify=True)

    vc_no_images = copy.deepcopy(vc_res)
    vc_no_images["credential"]["vc"]["credentialSubject"]["image"] = "REDACTED"
    vc_no_images["credential"]["vc"]["credentialSubject"]["theme"]["icon"] = "REDACTED"
    pp_json(vc_no_images)
    return vc_res
