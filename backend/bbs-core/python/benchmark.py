import bbs_core
import pandas as pd
from abc import ABC, abstractmethod
import json
import random
import string
import time
import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from sd_jwt.issuer import SDJWTIssuer
from sd_jwt.holder import SDJWTHolder
from sd_jwt.verifier import SDJWTVerifier
from jwcrypto import jwk
from sd_jwt.common import SDObj

random.seed(0)


class BechmarkMethodHandler(ABC):
    def __init__(self, credential: dict = {}, to_reveal_keys: list = []):
        super().__init__()
        self.credential = credential
        self.to_reveal_keys = to_reveal_keys

    @abstractmethod
    def generate_key_pair(self):
        pass

    @abstractmethod
    def sign_messages(self):
        pass

    @abstractmethod
    def generate_proof(self):
        pass

    @abstractmethod
    def verify_proof(self):
        pass


class BBS_plus(BechmarkMethodHandler):
    def __init__(self, credential: dict = {}, to_reveal_keys: list = []):
        super().__init__(credential, to_reveal_keys)

        self.messages = [json.dumps({key: credential[key]}, ensure_ascii=False)
                         for key in sorted(credential.keys())]

        self.revealed_indexes = [
            list(credential.keys()).index(key) for key in to_reveal_keys]

        self.total_messages = len(self.messages)

    def run(self):
        self.generate_key_pair()
        self.sign_messages()
        self.generate_proof()
        print(self.verify_proof())

    def generate_key_pair(self):
        key_pair = bbs_core.GenerateKeyPair().generate_key_pair()
        self.dpub_key_bytes = key_pair.dpub_key_bytes
        self.priv_key_bytes = key_pair.priv_key_bytes
        return self.dpub_key_bytes, self.priv_key_bytes

    def sign_messages(self):
        signer = bbs_core.SignRequest(
            self.messages, self.dpub_key_bytes, self.priv_key_bytes)
        sign_result = signer.sign_messages()
        self.signature_bytes = sign_result.signature
        return self.signature_bytes

    def generate_proof(self):
        proof_generator = bbs_core.GenerateProofRequest(
            self.dpub_key_bytes, self.signature_bytes, self.revealed_indexes, self.messages)
        proof_result = proof_generator.generate_proof()

        self.nonce_bytes = proof_result.nonce_bytes
        self.proof_request_bytes = proof_result.proof_request_bytes
        self.proof_bytes = proof_result.proof_bytes
        self.disclosed_messages = [self.messages[i]
                                   for i in self.revealed_indexes]
        return self.nonce_bytes, self.proof_request_bytes, self.proof_bytes, self.disclosed_messages

    def verify_proof(self):
        verifier = bbs_core.VerifyRequest(
            self.nonce_bytes, self.proof_request_bytes, self.proof_bytes, self.disclosed_messages, self.dpub_key_bytes, self.total_messages)
        verify_result = verifier.is_valid()
        return verify_result


class W3C_JWT(BechmarkMethodHandler):
    def __init__(self, credential={}, to_reveal_keys=[]):
        super().__init__(credential, to_reveal_keys)
        self.holder_private_key = ec.generate_private_key(ec.SECP256R1())
        self.holder_public_key = self.holder_private_key.public_key()

    def generate_key_pair(self):
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        return self.public_key, self.private_key

    def sign_messages(self):
        self.signed_messages = jwt.encode(
            self.credential, self.private_key, algorithm="ES256")
        return self.signed_messages

    def generate_proof(self):
        self.proof = jwt.encode(
            self.credential, self.holder_private_key, algorithm="ES256")
        return self.proof

    def verify_proof(self):
        return jwt.decode(self.proof, self.holder_public_key, algorithms=["ES256"])


class SD_JWT(BechmarkMethodHandler):
    def __init__(self, credential={}, to_reveal_keys=[]):
        super().__init__(credential, to_reveal_keys)
        self.credential = {SDObj(key): f"{value}" for key,
                           value in credential.items()}
        self.claims_to_disclose = {key: False for key in credential.keys()}
        for key in to_reveal_keys:
            self.claims_to_disclose[key] = True

    def generate_key_pair(self):
        self.private_key = jwk.JWK.generate(kty="EC", crv="P-256")
        self.public_key = self.private_key.public()
        return self.public_key, self.private_key

    def sign_messages(self):
        self.issuer = SDJWTIssuer(
            self.credential, self.private_key, add_decoy_claims=False)
        self.signed_messages = self.issuer.sd_jwt_issuance
        return self.signed_messages

    def generate_proof(self):
        holder = SDJWTHolder(self.signed_messages)
        holder.create_presentation(
            self.claims_to_disclose, sign_alg="ES256")
        self.proof = holder.sd_jwt_presentation
        return self.proof

    def verify_proof(self):
        def get_issuer_key(issuer, header_parameters):
            return self.public_key
        verifier = SDJWTVerifier(self.proof, get_issuer_key)
        verified = verifier.get_verified_payload()
        return verified


def generate_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_test_data(key_length, value_length, credential_length, to_reveal_keys_length):
    credential = {generate_string(key_length): generate_string(
        value_length) for _ in range(credential_length)}

    credential = dict(sorted(credential.items()))

    to_reveal_keys = random.sample(
        list(credential.keys()), to_reveal_keys_length)
    to_reveal_keys = sorted(to_reveal_keys)
    return credential, to_reveal_keys


def benchmark():
    df = pd.DataFrame(columns=["class_name", "loop_count",
                      "variance_description", "variance_value", "variance_title", "time"])

    def benchmark_method_with_loops(df, instantiated_class, loop_count, method, variance_description, variance_value, variance_title):
        start = time.time()
        for _ in range(loop_count):
            method()
        end = time.time()

        # Add column named count to df if it doesn't exist
        class_name = instantiated_class.__class__.__name__
        time_taken = end - start
        df.loc[len(df)] = [class_name, loop_count, variance_description,
                           variance_value, variance_title, time_taken]

    def benchmark_varying_credential_or_disclosure(df, credential_classes, credential_generator, loops, variances, variance_description, variance_title):
        for variance in variances:
            for credential_class in credential_classes:
                for loop in loops:
                    print(variance_title, credential_class.__name__, loop, variance)
                    credential, to_reveal_keys = credential_generator(variance)
                    instantiated_credential_class = credential_class(
                        credential, to_reveal_keys)
                    instantiated_credential_class.generate_key_pair()
                    benchmark_method_with_loops(
                        df, instantiated_credential_class, loop, instantiated_credential_class.sign_messages, variance_description, variance, "Signing:" + variance_title)
                    benchmark_method_with_loops(
                        df, instantiated_credential_class, loop, instantiated_credential_class.generate_proof, variance_description, variance, "Proof Generation:" + variance_title)
                    benchmark_method_with_loops(
                        df, instantiated_credential_class, loop, instantiated_credential_class.verify_proof, variance_description, variance, "Verification:" + variance_title)

    ########################### KEY GENERATION BENCHMARK ############################
    loop_counts = [10, 100, 1000] + [i * 10000 for i in range(1, 5)]
    loop_counts.sort()
    credential_classes = [BBS_plus(), W3C_JWT(), SD_JWT()]
    for credential_class in credential_classes:
        for loop_count in loop_counts:
            print(credential_class.__class__.__name__, loop_count)
            benchmark_method_with_loops(
                df, credential_class, loop_count, credential_class.generate_key_pair, "Amount of keys generated", loop_count, "Key Generation Benchmark")

    ########################### SIGN PROOF VERIFY BENCHMARKS ############################
    loops = [10, 50, 100]
    credential_classes = [BBS_plus, W3C_JWT, SD_JWT]

    ############# VARYING CREDENTIAL SIZE #############
    credential_lengths = [1, 10, 100, 200, 300, 400, 500]
    credential_lengths.sort()
    def vary_credential_sizes(x): return generate_test_data(10, 10, x, 1)
    benchmark_varying_credential_or_disclosure(
        df, credential_classes, vary_credential_sizes, loops, credential_lengths, "Amount of entries in credential", "Vertical Credential Size Benchmark")

    ############# VARYING VALUES LENGTH #############
    values_lengths = [1, 10, 100, 200, 500, 1000, 1500, 2000, 2500, 3000]
    values_lengths.sort()
    def vary_values_length(x): return generate_test_data(10, x, 100, 1)
    benchmark_varying_credential_or_disclosure(
        df, credential_classes, vary_values_length, loops, values_lengths, "Length of entry values in credential", "Horizontal Credential Size Benchmark")

    ############# VARYING REVEAL LENGTH #############
    reveal_lengths = [1] + [i * 100 for i in range(1, 10)]
    reveal_lengths.sort()
    def vary_reveal_length(x): return generate_test_data(10, 10, 1000, x)
    benchmark_varying_credential_or_disclosure(
        df, credential_classes, vary_reveal_length, loops, reveal_lengths, "Amount of entries to reveal in credential", "Reveal Size Benchmark")

    df.to_csv("benchmark_results.csv")


if __name__ == "__main__":
    start_time = time.time()
    benchmark()
    print("Benchmark took", time.time() - start_time, "seconds")
    # format seconds to hh:mm:ss
    print(time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time)))
