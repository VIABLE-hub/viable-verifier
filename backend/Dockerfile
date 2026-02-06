# StudentVC Docker with REAL BBS+ Core Compilation
FROM python:3.11-slim AS base

# Install system dependencies for Rust, BBS+ core compilation, and application
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    build-essential \
    pkg-config \
    libssl-dev \
    libclang-dev \
    openssl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# BBS+ core build stage - this builds the Linux-compatible bindings
FROM base AS bbs-builder

# Install Rust (required for BBS+ core compilation)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install maturin (better interface for Python-Rust builds)
RUN pip install --no-cache-dir maturin

# Copy BBS+ core source code
COPY bbs-core/ /app/bbs-core/

# Build the BBS+ core
WORKDIR /app/bbs-core
RUN mkdir -p python
RUN rm -f python/bbs_core.py python/uniffi_bbs_core.dll python/libuniffi_bbs_core.so python/libuniffi_bbs_core.dylib
RUN cargo build --lib --release
RUN cargo run --features=uniffi/cli --bin uniffi-bindgen generate src/lib.udl --language python --out-dir target/python
RUN cp target/release/libbbs_core.so python/libuniffi_bbs_core.so
RUN cp target/python/bbs_core.py python/bbs_core.py

# Test the BBS+ core (optional but recommended)
WORKDIR /app/bbs-core/python
RUN python -c "import bbs_core; print('✅ BBS+ core built and loaded successfully'); key_pair = bbs_core.GenerateKeyPair().generate_key_pair(); print(f'✅ Key pair generated: Public key: {len(key_pair.dpub_key_bytes)} bytes, Private key: {len(key_pair.priv_key_bytes)} bytes')"

# Main application stage
FROM base AS app

# Copy application code
COPY . .

# Copy the BBS+ core files from the bbs-builder stage
COPY --from=bbs-builder /app/bbs-core/python/libuniffi_bbs_core.so /app/
COPY --from=bbs-builder /app/bbs-core/python/bbs_core.py /app/

# Create required directories
RUN mkdir -p /app/instance
RUN mkdir -p /app/data
RUN mkdir -p /app/static

# Make sure scripts are executable
RUN chmod +x /app/src/static/js/*.js

# Set Python path to include the app directory
ENV PYTHONPATH=/app

# Environment settings
ENV SERVER_HOST=0.0.0.0
ENV SERVER_PORT=8080
ENV DATABASE_PATH=/app/data

# Expose port for web interface
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]

# BBS test target - use this for isolated BBS testing
FROM bbs-builder AS bbs-test

# Create a test script
WORKDIR /app/bbs-core/python
RUN echo 'import bbs_core\nprint("✅ BBS+ core loaded successfully on Linux")\n\nkey_gen = bbs_core.GenerateKeyPair()\nkey_pair = key_gen.generate_key_pair()\n\npublic_key = key_pair.dpub_key_bytes\nprivate_key = key_pair.priv_key_bytes\n\nprint(f"✅ Public key (dpub_key_bytes): {len(public_key)} bytes")\nprint(f"✅ Private key (priv_key_bytes): {len(private_key)} bytes")\n\nprint("\\n✅ BBS+ TEST SUCCESSFUL! The library works correctly on Linux.")' > test.py

# Run the test on container start
CMD ["python", "test.py"]
