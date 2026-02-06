from cfg import host, client_id, private_key, code_verifier, code_challenge
from utils import pp_json, random_string
import requests
import jwt
from urllib.parse import urlparse, parse_qs


def get_authotize(offer_uuid):
    args = {}
    args["response_type"] = "code"
    args["client_id"] = client_id
    args["redirect_uri"] = "https://example.com"  # optional
    args["code_challenge_method"] = "S256"
    args["code_challenge"] = code_challenge
    args["state"] = random_string(10)
    args["nonce"] = random_string(10)
    args["issuer_state"] = offer_uuid

    response = requests.get(
        f"{host}authorize",
        allow_redirects=False,
        verify=False,
        params=args
    )
    # snach the redirect url and parse the parameters from it
    redirected_to = response.headers["location"]
    parsed_url = urlparse(redirected_to)
    auth_redirect = parse_qs(parsed_url.query)
    pp_json(auth_redirect)
    return auth_redirect


def direct_post(offer_uuid):

    id_token_payload = {
        "issuer_state": offer_uuid,
        "iss": client_id,
        "nonce": random_string(),      # Replay protection
        "state": random_string(10),
        "code_challenge": code_challenge,
    }

    id_token = jwt.encode(id_token_payload, private_key, algorithm="ES256")
    payload = {
        "id_token": id_token,
        "state": random_string(10),
    }

    response = requests.post(
        f"{host}direct_post",
        allow_redirects=False,
        verify=False,
        params=payload
    )

    redirected_to = response.headers["location"]
    parsed_url = urlparse(redirected_to)
    direct_post_redirect = parse_qs(parsed_url.query)
    pp_json(direct_post_redirect)
    return direct_post_redirect


def authorize(offer_uuid):
    get_authotize(offer_uuid)
    res = direct_post(offer_uuid)
    return res["code"][0]
