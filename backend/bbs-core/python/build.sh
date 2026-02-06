#!/bin/bash
echo "Building BBS Core"
# Navigate to the parent directory
cd ..

# Remove the Python files if they exist
rm -f python/bbs_core.py
rm -f python/uniffi_bbs_core.dll
rm -f python/libuniffi_bbs_core.so
rm -f python/libuniffi_bbs_core.dylib

# Generate the DLL
cargo build --lib --release

# Generate Python bindings
cargo run --features=uniffi/cli --bin uniffi-bindgen generate src/lib.udl --language python --out-dir target/python

# Move and rename the so for Linux
mv target/release/libbbs_core.so python/libuniffi_bbs_core.so

# Move and rename the dylib for Mac
mv target/release/libbbs_core.dylib python/libuniffi_bbs_core.dylib

# Move bindings to the correct location
mv target/python/bbs_core.py python/bbs_core.py

# Navigate to the Python directory
cd python

# Run main.py
python3 main.py
