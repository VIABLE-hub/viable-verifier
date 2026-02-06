from utils import random_string, get_keys, generate_pkce_challenge, generate_holder_did
host = "https://127.0.0.1:8080/"
presentation_host = host + "verifier/"
code_verifier, code_challenge = generate_pkce_challenge()
private_key, public_key = get_keys()
holder_did = generate_holder_did(public_key)
client_id = holder_did
