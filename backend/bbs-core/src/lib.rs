uniffi::include_scaffolding!("lib");
use bbs::pm_hidden;
use bbs::pm_revealed;
use bbs::prelude::*;

pub struct GenerateKeyPair {}
pub struct KeyPair {
    pub dpub_key_bytes: Vec<u8>,
    pub priv_key_bytes: Vec<u8>,
}

impl GenerateKeyPair {
    pub fn new() -> Self {
        Self {}
    }

    pub fn generate_key_pair(&self) -> KeyPair {
        let (dpk, sk) = Issuer::new_short_keys(None);
        KeyPair {
            dpub_key_bytes: dpk.to_bytes_compressed_form().to_vec(),
            priv_key_bytes: sk.to_bytes_compressed_form().to_vec(),
        }
    }
}

pub struct SignRequest {
    pub messages: Vec<String>,
    pub dpub_key_bytes: Vec<u8>,
    pub priv_key_bytes: Vec<u8>,
}

pub struct SignResult {
    pub pub_key_bytes: Vec<u8>,
    pub signature: Vec<u8>,
}

impl SignRequest {
    pub fn new(
        messages: Vec<String>,
        dpub_key_bytes: Vec<u8>,
        priv_key_bytes: Vec<u8>,
    ) -> SignRequest {
        Self {
            messages,
            dpub_key_bytes,
            priv_key_bytes,
        }
    }

    fn sign_messages(&self) -> SignResult {
        let message_count = self.messages.len();

        let dpk = DeterministicPublicKey::try_from(self.dpub_key_bytes.as_slice())
            .expect("Invalid deterministic public key");

        let sk = SecretKey::try_from(self.priv_key_bytes.as_slice()).expect("Invalid secret key");
        let pk = dpk
            .to_public_key(message_count)
            .expect("Generating full public key failed");

        let messages = self
            .messages
            .iter()
            .map(|m| SignatureMessage::hash(m.as_bytes()))
            .collect::<Vec<SignatureMessage>>();

        let signature = Signature::new(messages.as_slice(), &sk, &pk).unwrap();
        SignResult {
            pub_key_bytes: pk.to_bytes_compressed_form().to_vec(),
            signature: signature.to_bytes_compressed_form().to_vec(),
        }
    }
}

pub struct ProofResult {
    pub nonce_bytes: Vec<u8>,
    pub proof_request_bytes: Vec<u8>,
    pub proof_bytes: Vec<u8>,
}

pub struct GenerateProofRequest {
    pub dpub_key_bytes: Vec<u8>,
    pub signature_bytes: Vec<u8>,
    pub revealed_indices: Vec<usize>,
    pub messages: Vec<String>,
}

impl GenerateProofRequest {
    pub fn new(
        dpub_key_bytes: Vec<u8>,
        signature_bytes: Vec<u8>,
        revealed_indices: Vec<u64>,
        messages: Vec<String>,
    ) -> Self {
        // since were on x64 systems anyways these days, its safe to just cast u64 to usize, since uniFFI doesnt directly support usize
        Self {
            dpub_key_bytes,
            signature_bytes,
            revealed_indices: revealed_indices.into_iter().map(|x| x as usize).collect(),
            messages,
        }
    }

    pub fn generate_proof(&self) -> ProofResult {
        let dpk = DeterministicPublicKey::try_from(self.dpub_key_bytes.as_slice())
            .expect("Invalid deterministic public key");
        let pk = dpk
            .to_public_key(self.messages.len())
            .expect("Generating full public key failed");
        let signature =
            Signature::try_from(self.signature_bytes.as_slice()).expect("Invalid signature");
        let nonce = Verifier::generate_proof_nonce();
        let proof_request = Verifier::new_proof_request(&self.revealed_indices, &pk).unwrap();

        let proof_messages = self
            .messages
            .iter()
            .enumerate()
            .map(|(i, m)| {
                if self.revealed_indices.contains(&i) {
                    pm_revealed!(m.as_bytes())
                } else {
                    pm_hidden!(m.as_bytes())
                }
            })
            .collect::<Vec<_>>();

        let pok =
            Prover::commit_signature_pok(&proof_request, proof_messages.as_slice(), &signature)
                .unwrap();

        // complete other zkps as desired and compute `challenge_hash`
        // add bytes from other proofs

        let mut challenge_bytes = Vec::new();
        challenge_bytes.extend_from_slice(pok.to_bytes().as_slice());
        challenge_bytes.extend_from_slice(nonce.to_bytes_uncompressed_form().as_slice());

        let challenge = ProofChallenge::hash(&challenge_bytes);

        let proof = Prover::generate_signature_pok(pok, &challenge).unwrap();
        ProofResult {
            nonce_bytes: nonce.to_bytes_compressed_form().to_vec(),
            proof_request_bytes: proof_request.to_bytes_compressed_form().to_vec(),
            proof_bytes: proof.to_bytes_compressed_form().to_vec(),
        }
    }
}

pub struct VerifyRequest {
    pub nonce_bytes: Vec<u8>,
    pub proof_request_bytes: Vec<u8>,
    pub proof_bytes: Vec<u8>,
    pub disclosed_messages: Vec<String>,
    pub dpub_key_bytes: Vec<u8>,
    pub total_message_count: usize,
}

impl VerifyRequest {
    pub fn new(
        nonce_bytes: Vec<u8>,
        proof_request_bytes: Vec<u8>,
        proof_bytes: Vec<u8>,
        disclosed_messages: Vec<String>,
        dpub_key_bytes: Vec<u8>,
        total_message_count: u64,
    ) -> VerifyRequest {
        Self {
            nonce_bytes,
            proof_request_bytes,
            proof_bytes,
            disclosed_messages,
            dpub_key_bytes,
            total_message_count: total_message_count as usize,
        }
    }

    fn is_valid(&self) -> String {
        let dpk = DeterministicPublicKey::try_from(self.dpub_key_bytes.as_slice())
            .expect("Invalid deterministic public key");
        let pk = dpk
            .to_public_key(self.total_message_count)
            .expect("generating full public key failed");
        let nonce = ProofNonce::try_from(self.nonce_bytes.as_slice()).expect("Invalid nonce");
        let proof_request = ProofRequest::try_from(self.proof_request_bytes.as_slice())
            .expect("Invalid proof request");
        let proof = SignatureProof::try_from(self.proof_bytes.as_slice()).expect("Invalid proof");

        // assert pk matches pk in proof_request
        if pk != proof_request.verification_key {
            return "public key mismatch".to_string();
        }

        match Verifier::verify_signature_pok(&proof_request, &proof, &nonce) {
            Ok(messages) => {
                let match_attempt = self
                    .disclosed_messages
                    .iter()
                    .zip(messages.iter())
                    .all(|(m, msg)| SignatureMessage::hash(m.as_bytes()) == *msg);
                if match_attempt {
                    return "true".to_string();
                } else {
                    return "matchin messages to presentation failed".to_string();
                }
            }
            Err(_) => {
                return "verification failed".to_string();
            }
        }
    }
}
