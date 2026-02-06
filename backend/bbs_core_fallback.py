import base64
import json
import secrets

class SignResult:
    def __init__(self):
        # Create a dummy signature for testing
        self.signature = b'DOCKER_FALLBACK_SIGNATURE_FOR_TESTING'

class SignRequest:
    def __init__(self, messages, public_key, secret_key):
        self.messages = messages
        self.public_key = public_key
        self.secret_key = secret_key
        print(f'⚠️ BBS+ SignRequest called in Docker fallback mode with {len(messages)} messages')
    
    def sign_messages(self):
        print('⚠️ Using fallback signature - for testing only!')
        return SignResult()

class KeyPair:
    def __init__(self):
        # Generate dummy keys for testing
        self.secret_key = secrets.token_bytes(32)  # 32 bytes for secret key
        self.public_key = secrets.token_bytes(96)  # 96 bytes for public key (typical BBS+ size)
        print(f'⚠️ Generated fallback BBS+ keypair - secret: {len(self.secret_key)} bytes, public: {len(self.public_key)} bytes')

class GenerateKeyPair:
    def __init__(self):
        print('⚠️ BBS+ GenerateKeyPair called in Docker fallback mode')
    
    def generate_key_pair(self):
        print('⚠️ Generating fallback BBS+ keypair - for testing only!')
        return KeyPair()

# Additional classes that might be needed
class VerifyRequest:
    def __init__(self, *args, **kwargs):
        print('⚠️ BBS+ VerifyRequest called in Docker fallback mode')
        self.args = args
        self.kwargs = kwargs
    
    def is_valid(self):
        print('⚠️ Using fallback verification - always returns True for testing!')
        return True

class ProofRequest:
    def __init__(self, *args, **kwargs):
        print('⚠️ BBS+ ProofRequest called in Docker fallback mode')
        self.args = args
        self.kwargs = kwargs

print('⚠️ Docker BBS+ fallback mode active - all cryptographic operations are for testing only!') 