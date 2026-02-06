# Key Usage Explanation for StudentVC System

## 🔐 BBS+ Keys (BBS+ Credential Signing)

**Purpose**: Enable **selective disclosure** and **zero-knowledge proofs** for Verifiable Credentials

### How BBS+ Keys Work:
1. **Issuer Signs**: The issuer uses the BBS+ **private key** to create a special signature over ALL credential fields
2. **Holder Derives**: The wallet/holder can create a **derived proof** that reveals only selected fields
3. **Verifier Checks**: The verifier uses the BBS+ **public key** to verify the zero-knowledge proof

### Key Features:
- **Selective Disclosure**: Reveal only `firstName` while keeping `lastName` and `studentId` hidden
- **Unlinkability**: Each presentation looks different (can't track user across verifications)
- **Zero-Knowledge**: Proves you have a valid credential without revealing all data

### In StudentVC:
```
Issuer → Signs full credential with BBS+ private key
Wallet → Creates ZK proof revealing only selected fields  
Verifier → Verifies proof with BBS+ public key
```

## 🔏 JWT Keys (JWT Envelope Signing)

**Purpose**: Provide **transport security** and **issuer authentication** for the credential

### How JWT Keys Work:
1. **Outer Envelope**: The entire VC (including BBS+ signature) is wrapped in a JWT
2. **Digital Signature**: The JWT is signed with the issuer's Ed25519 **private key**
3. **DID Resolution**: The verifier resolves the issuer's DID to get the **public key**

### Key Features:
- **Issuer Authentication**: Proves which university issued the credential
- **Integrity Protection**: Ensures credential wasn't tampered with
- **Standard Format**: Compatible with OpenID4VC protocols

### The DID (Decentralized Identifier):
```
did:key:zXwpQjZaoASZf1Q9mhhx4o...
```
- **Globally Unique**: Each system has a different DID
- **Self-Describing**: Contains the public key within the identifier
- **Resolvable**: Verifiers can extract the public key from the DID

## 🎯 How They Work Together

```
1. ISSUANCE:
   StudentVC Issuer
   ├── Creates credential with student data
   ├── Signs with BBS+ private key (enables selective disclosure)
   └── Wraps in JWT signed with Ed25519 key (proves issuer identity)

2. PRESENTATION:
   Student Wallet
   ├── Receives full credential
   ├── User selects fields to reveal (e.g., only firstName)
   ├── Creates BBS+ zero-knowledge proof
   └── Sends proof to verifier

3. VERIFICATION:
   StudentVC Verifier
   ├── Resolves issuer DID → gets Ed25519 public key
   ├── Verifies JWT signature (authentic issuer?)
   ├── Extracts BBS+ public key from credential
   └── Verifies zero-knowledge proof (valid selective disclosure?)
```

## 🔑 Security Benefits

1. **Privacy-Preserving**: Students reveal only necessary information
2. **Single-University**: Each system  has unique keys
3. **Cryptographically Secure**: Can't forge credentials or proofs
4. **Future-Proof**: BBS+ is a cutting-edge privacy technology

## 📊 Key Lifecycle

- **Created**: When system first needs to issue credentials
- **Expires**: After 1 year (configurable)
- **Rotation**: Old credentials remain verifiable with old public keys
- **Backup**: Keys stored in `backend/src/systems/instances/{system}/keys/`

Each system's keys are completely isolated, ensuring that a compromise of one university's keys doesn't affect others. 