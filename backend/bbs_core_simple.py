# Simple Mock BBS+ Core for Deployment Testing
# This is a temporary implementation to get containers running
# TODO: Replace with full BBS+ implementation when Rust library is available

class KeyPair:
    def __init__(self, *, dpub_key_bytes: bytes, priv_key_bytes: bytes):
        self.dpub_key_bytes = dpub_key_bytes
        self.priv_key_bytes = priv_key_bytes

class SignResult:
    def __init__(self, *, pub_key_bytes: bytes, signature: bytes):
        self.pub_key_bytes = pub_key_bytes
        self.signature = signature

class ProofResult:
    def __init__(self, *, nonce_bytes: bytes, proof_request_bytes: bytes, proof_bytes: bytes):
        self.nonce_bytes = nonce_bytes
        self.proof_request_bytes = proof_request_bytes
        self.proof_bytes = proof_bytes

class GenerateKeyPair:
    def __init__(self):
        pass
    
    def generate_key_pair(self):
        # Mock key generation
        return KeyPair(
            dpub_key_bytes=b"mock_dpub_key_32_bytes_long_data",
            priv_key_bytes=b"mock_priv_key_32_bytes_long_data"
        )

class SignRequest:
    def __init__(self, messages, dpub_key_bytes, priv_key_bytes):
        self.messages = messages
        self.dpub_key_bytes = dpub_key_bytes
        self.priv_key_bytes = priv_key_bytes
    
    def sign_messages(self):
        # Mock signing
        return SignResult(
            pub_key_bytes=self.dpub_key_bytes,
            signature=b"mock_signature_64_bytes_long_data_placeholder_for_testing_deployment"
        )

class GenerateProofRequest:
    def __init__(self, pub_key_bytes, signature_bytes, revealed_indices, messages):
        self.pub_key_bytes = pub_key_bytes
        self.signature_bytes = signature_bytes
        self.revealed_indices = revealed_indices
        self.messages = messages
    
    def generate_proof(self):
        # Mock proof generation
        return ProofResult(
            nonce_bytes=b"mock_nonce_32_bytes_data_here",
            proof_request_bytes=b"mock_proof_request_data_here",
            proof_bytes=b"mock_proof_bytes_data_here_for_testing"
        )

class VerifyRequest:
    def __init__(self, nonce_bytes, proof_request_bytes, proof_bytes, disclosed_messages, dpub_key_bytes, total_message_count):
        self.nonce_bytes = nonce_bytes
        self.proof_request_bytes = proof_request_bytes
        self.proof_bytes = proof_bytes
        self.disclosed_messages = disclosed_messages
        self.dpub_key_bytes = dpub_key_bytes
        self.total_message_count = total_message_count
    
    def is_valid(self):
        # Mock verification - always return valid for deployment testing
        return "valid"

# For backwards compatibility
class InternalError(Exception):
    pass 