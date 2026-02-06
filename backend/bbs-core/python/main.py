import bbs_core


def main():
    # ISSUER: generate keys
    dpub_key_bytes, priv_key_bytes = generate_key_pair()

    # ISSUER: sign messages
    messages = ["message_1", "message_2", "message_3"]
    signature_bytes = sign_messages(
        dpub_key_bytes, priv_key_bytes, messages)

    # HOLDER: proove messages
    revealed_indexes = [0, 2]
    nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages = generate_proof(
        dpub_key_bytes, messages, signature_bytes, revealed_indexes)

    # VERIFIER: verify proof
    total_messages = len(messages)
    verify_result = verify_proof(
        dpub_key_bytes, nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages, total_messages)
    print(verify_result)


def verify_proof(dpub_key_bytes, nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages, total_messages):
    verifier = bbs_core.VerifyRequest(
        nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages, dpub_key_bytes, total_messages)
    verify_result = verifier.is_valid()
    return verify_result


def generate_proof(dpub_key_bytes, messages, signature_bytes, revealed_indexes):
    proof_generator = bbs_core.GenerateProofRequest(
        dpub_key_bytes, signature_bytes, revealed_indexes, messages)
    proof_result = proof_generator.generate_proof()

    nonce_bytes = proof_result.nonce_bytes
    proof_request_bytes = proof_result.proof_request_bytes
    proof_bytes = proof_result.proof_bytes
    disclosed_messages = [messages[i] for i in revealed_indexes]
    return nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages


def sign_messages(dpub_key_bytes, priv_key_bytes, messages):
    signer = bbs_core.SignRequest(messages, dpub_key_bytes, priv_key_bytes)
    sign_result = signer.sign_messages()
    return sign_result.signature


def generate_key_pair():
    key_pair = bbs_core.GenerateKeyPair().generate_key_pair()
    dpub_key_bytes = key_pair.dpub_key_bytes
    priv_key_bytes = key_pair.priv_key_bytes
    return dpub_key_bytes, priv_key_bytes


if __name__ == "__main__":
    main()
