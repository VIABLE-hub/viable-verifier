from cfg import host, client_id, private_key, code_verifier, code_challenge
from utils import pp_json, random_string
import requests
import jwt
from urllib.parse import urlparse, parse_qs


def get_token(code):
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://example.com",
        "code_verifier": code_verifier,
        "client_id": client_id,
    }

    response = requests.post(
        f"{host}token",
        allow_redirects=False,
        verify=False,
        data=payload,
        params=payload
    )

    pp_json(response.json())
    return response.json()
