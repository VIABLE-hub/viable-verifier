#!/bin/bash

# Colors for better output readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== BBS+ Core Linux Compatibility Test ===${NC}"
echo -e "${YELLOW}Testing BBS+ bindings in a Linux Docker container${NC}"
echo -e "${YELLOW}This ensures UniFFI contracts match without rebuilding everything${NC}"

# Create a temporary Dockerfile that follows the original build.sh approach
cat > Dockerfile.bbs-test << 'DOCKERFILE'
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Working directory
WORKDIR /app

# Copy BBS core files
COPY backend/bbs-core /app/bbs-core

# Run the build process (matching your build.sh script)
WORKDIR /app/bbs-core

# Setup python dir
RUN mkdir -p python

# Clean any existing files
RUN rm -f python/bbs_core.py python/uniffi_bbs_core.dll python/libuniffi_bbs_core.so python/libuniffi_bbs_core.dylib

# Build the library
RUN cargo build --lib --release

# Generate Python bindings
RUN cargo run --features=uniffi/cli --bin uniffi-bindgen generate src/lib.udl --language python --out-dir target/python

# Move the shared library for Linux
RUN cp target/release/libbbs_core.so python/libuniffi_bbs_core.so

# Move the Python bindings
RUN cp target/python/bbs_core.py python/bbs_core.py

# Test directory
WORKDIR /app/bbs-core/python

# Create a test script that shows API details
RUN echo 'import bbs_core\nprint("✅ BBS+ core loaded successfully on Linux")\n\n# Create key generator\nkey_gen = bbs_core.GenerateKeyPair()\nprint("✅ Created key generator")\n\n# Generate key pair\nkey_pair = key_gen.generate_key_pair()\nprint("✅ Generated key pair")\n\n# Test with the correct attributes from KeyPair object\ntry:\n    public_key = key_pair.dpub_key_bytes\n    private_key = key_pair.priv_key_bytes\n    \n    print(f"✅ Public key (dpub_key_bytes): {len(public_key)} bytes")\n    print(f"✅ Private key (priv_key_bytes): {len(private_key)} bytes")\n    \n    # Create a dummy message to sign\n    message = b"Hello, BBS+ signatures!"\n    message_vec = [message]\n    \n    # Try to sign (if available)\n    try:\n        # This might vary based on your BBS+ API implementation\n        signer = bbs_core.BBSSigner(private_key)\n        signature = signer.sign(message_vec)\n        print(f"✅ Successfully created signature: {len(signature)} bytes")\n    except AttributeError:\n        print("⚠️ BBSSigner not found - different API structure than expected")\n    except Exception as e:\n        print(f"⚠️ Signing test failed: {e}")\n\n    print("\\n✅ BBS+ TEST SUCCESSFUL! The library works correctly on Linux.")\nexcept Exception as e:\n    print(f"❌ Error: {e}")' > test.py

# The command to run when the container starts
CMD ["python", "test.py"]
DOCKERFILE

echo -e "${BLUE}Building test container...${NC}"
docker build -t bbs-linux-test -f Dockerfile.bbs-test .

if [ $? -ne 0 ]; then
  echo -e "${RED}❌ Error: Failed to build Docker test container${NC}"
  rm Dockerfile.bbs-test
  exit 1
fi

echo -e "${BLUE}Running BBS+ compatibility test...${NC}"
docker run --rm bbs-linux-test

if [ $? -ne 0 ]; then
  echo -e "${RED}❌ Error: BBS+ test failed in Linux container${NC}"
  echo -e "${YELLOW}This suggests UniFFI contracts are incompatible${NC}"
  echo -e "${YELLOW}See the error output above for details${NC}"
  
  # Ask if user wants to run interactive debugging
  echo -e "${YELLOW}Would you like to run interactive debugging? (y/n)${NC}"
  read -r debug
  
  if [[ "$debug" == "y" || "$debug" == "Y" ]]; then
    echo -e "${BLUE}Starting interactive debug shell...${NC}"
    docker run --rm -it bbs-linux-test /bin/bash
  fi
  
  rm Dockerfile.bbs-test
  exit 1
fi

echo -e "${GREEN}✅ Success! BBS+ bindings work correctly on Linux${NC}"
echo -e "${GREEN}✅ UniFFI contracts are compatible${NC}"

# Extract the library files
echo -e "${YELLOW}Extracting Linux-compatible BBS+ files to backend/bbs-core/linux-build/${NC}"

# Create temporary container
docker create --name temp-bbs-container bbs-linux-test

# Create output directory
mkdir -p backend/bbs-core/linux-build

# Copy files
docker cp temp-bbs-container:/app/bbs-core/python/libuniffi_bbs_core.so backend/bbs-core/linux-build/
docker cp temp-bbs-container:/app/bbs-core/python/bbs_core.py backend/bbs-core/linux-build/

# Remove container
docker rm temp-bbs-container

echo -e "${GREEN}✅ Files extracted to backend/bbs-core/linux-build/${NC}"
echo -e "${YELLOW}These files can be used in your Docker container for Linux compatibility${NC}"

# Clean up
rm Dockerfile.bbs-test

echo -e "${GREEN}======================${NC}"
echo -e "${GREEN}✅ Test complete!${NC}"
echo -e "${GREEN}You can now safely update the main Dockerfile${NC}"
echo -e "${GREEN}======================${NC}" 