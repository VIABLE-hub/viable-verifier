# bbs-core

This rust library provides a wrapper around the `bbs `crate for BBS+ signatures. `uniFFI` then provides bindings for all languages we use, e.g. Python, Rust, Kotlin.

## Features

### Signing Messages

```
interface SignRequest {
	constructor(sequence<string> messages);
	SignResult sign_messages();
};

dictionary SignResult {
    bytes pub_key_bytes;
    bytes signature;
};
```

### Generate Proof

```
interface GenerateProofRequest {
	constructor(bytes pub_key_bytes, bytes signature_bytes, sequence<u64> revealed_indices, sequence<string> messages);
	ProofResult generate_proof();
};

dictionary ProofResult {
    bytes nonce_bytes;
    bytes proof_request_bytes;
    bytes proof_bytes;
};
```



### Verify Proof

```
interface VerifyRequest {
	constructor(bytes nonce_bytes, bytes proof_request_bytes, bytes proof_bytes, sequence<string> disclosed_messages);
	boolean is_valid();
};
```



## How to use for Swift

1. Install `cargo-swift`

   ```
   cargo install cargo-swift
   ```

2. Run `cargo swift package --name BBSCoreIOS --platforms ios macos`

3. Install the generated Swift package inside the `BBSCoreIOS` folder like any other swift package

4. Import the library in your desired swift classes like any other external dependency:`import BBSCoreIOS`

5. Use the functions as described in the `src/lib.udl`, `uniFFI` provides all required bridges

## How to use for Python
1. Execute the `python/build.sh` or `python/build.ps1` script to build the python bindings

2. move the two newly generated files to your intended destination