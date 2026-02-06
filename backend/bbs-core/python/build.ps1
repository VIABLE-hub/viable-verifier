# Navigate to the parent directory
Set-Location ..

# Remove the python directory if it exists
Remove-Item  python/bbs_core.py
Remove-Item  python/uniffi_bbs_core.dll
Remove-Item  python/libuniffi_bbs_core.so
Remove-Item  python/libuniffi_bbs_core.dylib

# Generate DLL
cargo build --lib --release

# Generate Python bindings
cargo run --features=uniffi/cli --bin uniffi-bindgen generate src/lib.udl --language python --out-dir target/python

# Move and rename the DLL
Move-Item -Path target/release/bbs_core.dll -Destination python/uniffi_bbs_core.dll


# Move Bindings to the correct location
Move-Item -Path target/python/bbs_core.py -Destination python/bbs_core.py

# Navigate to the python directory
Set-Location python

# Run main.py
python main.py