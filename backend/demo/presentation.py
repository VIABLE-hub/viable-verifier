import requests
from cfg import presentation_host, private_key
from urllib.parse import urlparse, parse_qs
import jwt
from utils import pp_json, random_string
import json
import base64
import os
from flatten_json import flatten, unflatten
import importlib.util

bbs_core_path = os.path.join(os.path.dirname(
    __file__), "..", "bbs-core", "python", "bbs_core.py")
bbs_core_path = os.path.abspath(bbs_core_path)
spec = importlib.util.spec_from_file_location("bbs_core", bbs_core_path)
bbs_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bbs_core)


def get_authorization_request():
    response = requests.get(
        f"{presentation_host}request_uri",
        verify=False,
        allow_redirects=False
    )

    # response = openid4vp://?request_uri=https://server.example.com/presentation-request
    redirected_to = response.headers["location"]
    parsed_url = urlparse(redirected_to)
    authorization_request = parse_qs(parsed_url.query)
    pp_json(authorization_request)
    return authorization_request["request_uri"][0]


def resolve_authorization_request(request_uri):
    response = requests.post(
        request_uri,
        verify=False,
        allow_redirects=False
    )

    redirected_to = response.headers["location"]
    parsed_url = urlparse(redirected_to)
    res_authorization_request = parse_qs(parsed_url.query)
    pp_json(res_authorization_request)
    return res_authorization_request


def direct_post(vc, authorization_request):

    dest = authorization_request["response_uri"][0]
    vp_token = jwt.encode({"verifiable_credential": vc},
                          private_key, algorithm="ES256")
    presentation_submission = vc
    payload = {
        "vp_token": vp_token,
        "presentation_submission": presentation_submission
    }
    req = requests.post(
        dest,
        verify=False,
        allow_redirects=False,
        params=payload
    )

    print(req.text)
    return req


def process_vc(vc, mandatory=["iss", "sub", "nonce"], optional=['vc.credentialSubject.firstName']):
    payload = flatten(vc["credential"], '.')
    sorted_payload_keys = sorted(payload.keys())
    originaly_signed_values = [json.dumps(
        {key: payload[key]}, ensure_ascii=False) for key in sorted_payload_keys]

    to_include = mandatory + optional

    disclosed_field_indices = []

    # add any fields that start with to_include + "."
    for i, key in enumerate(sorted_payload_keys):
        for field in to_include:
            if key.startswith(field + ".") or key == field:
                disclosed_field_indices.append(i)

    disclosed_field_indices = sorted(disclosed_field_indices)

    extracted_values = {
        sorted_payload_keys[i]: payload[sorted_payload_keys[i]]
        for i in disclosed_field_indices}

    extracted_values = unflatten(extracted_values, '.')

    # Extract BBS+ metadata separately (will be moved outside values section)
    bbs_dpk_b64 = vc["credential"]["bbs_dpk"]
    total_messages = len(originaly_signed_values)

    dpk = base64.b64decode(bbs_dpk_b64)
    signature = base64.b64decode(vc["signature"])

    # pp_json(disclosed_field_indices)
    # pp_json(originaly_signed_values)

    proof_generator = bbs_core.GenerateProofRequest(
        dpk, signature, disclosed_field_indices, originaly_signed_values)
    proof_result = proof_generator.generate_proof()

    nonce_bytes = base64.b64encode(proof_result.nonce_bytes).decode()
    proof_request_bytes = base64.b64encode(
        proof_result.proof_request_bytes).decode()
    proof_bytes = base64.b64encode(proof_result.proof_bytes).decode()

    presentation_submission = {
        "nonce": nonce_bytes,
        "proof_req": proof_request_bytes,
        "proof": proof_bytes,
        "values": extracted_values,
        "bbs_dpk": bbs_dpk_b64,
        "total_messages": total_messages
    }
    # pp_json(extracted_values)
    return presentation_submission


def present(vc):
    request_uri = get_authorization_request()
    authorization_request = resolve_authorization_request(request_uri)
    mandatory_fields = authorization_request["presentation_definition"][0]
    mandatory_fields = json.loads(mandatory_fields)
    print(json.dumps(mandatory_fields, indent=4))
    mandatory_fields = mandatory_fields["mandatory_fields"]
    optional_fields = ['vc.credentialSubject.firstName']
    processed_vc = process_vc(vc, mandatory_fields, optional_fields)
    direct_post(processed_vc, authorization_request)
