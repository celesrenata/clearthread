# =============================================================================
# ClearThread Multi-Stage Dockerfile
# =============================================================================
# Build stages:
#   1. base        - Python base with system deps
#   2. gpu-base    - GPU libraries (CUDA/MPS/ROCm)
#   3. tauri-builder - Rust/Tauri build
#   4. final       - Combined runtime image
# =============================================================================

# ---------------------------------------------------------------------------
# Global ARG declarations (available to all stages)
# ---------------------------------------------------------------------------
ARG CUDA_VERSION=12.2.2
ARG PLATFORM=cuda

# ---------------------------------------------------------------------------
# Stage 1: Base Python image
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS base

LABEL maintainer="clearthread-dev@celesrenata.com"
LABEL description="ClearThread - Local-first Facebook/Messenger relationship analysis"

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System dependencies (including xz for nix install, build-essential for hnswlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsqlite3-0 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libfreetype6 \
    zlib1g \
    liblzma5 \
    xz-utils \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install nix (for flake support)
RUN for i in $(seq 1 10); do groupadd -f nixbld && useradd -G nixbld -M nixbld$i 2>/dev/null || true; done && \
    mkdir -m 0755 /nix && \
    curl -L https://nixos.org/nix/install | NIX_INSTALL_SH_NO_SUDO=true bash

# Set up Python environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml README.md /app/
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[dev]"

# ---------------------------------------------------------------------------
# Stage 2: GPU base (CUDA)
# ---------------------------------------------------------------------------
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu22.04 AS gpu-base

# Install MPS dependencies for Apple Silicon (cross-compile support)
# libmetal-dev is macOS-only, so we use || true to skip if unavailable
RUN apt-get update && apt-get install -y --no-install-recommends \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/* \
    || true

# CUDA libraries
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV CUDA_LIBRARY_PATH=/usr/local/cuda/lib64/stubs
ENV LD_LIBRARY_PATH=${CUDA_LIBRARY_PATH}

# ROCm support
ENV ROCM_PATH=/opt/rocm
ENV HSA_PATH=${ROCM_PATH}

# ---------------------------------------------------------------------------
# Stage 3: Tauri builder
# ---------------------------------------------------------------------------
FROM rust:1.85-bookworm AS tauri-builder

ARG TAURI_CLI_VERSION=2.0.0

# Install Tauri system dependencies first (needed before cargo build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libwebkit2gtk-4.1-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Tauri CLI with --locked for compatible dependencies
# tauri-bundler is a library (no executable), so we skip it
RUN cargo install tauri-cli@${TAURI_CLI_VERSION} --locked && \
    (cargo install tauri-bundler@${TAURI_CLI_VERSION} --locked || true)

# ---------------------------------------------------------------------------
# Stage 4: Final image
# ---------------------------------------------------------------------------
FROM base AS final

ARG PLATFORM
ARG CUDA_VERSION

# Copy GPU libraries if CUDA platform
COPY --from=gpu-base /usr/local/cuda /usr/local/cuda

# Copy Tauri binary (installed as cargo-tauri by cargo install)
COPY --from=tauri-builder /usr/local/cargo/bin/cargo-tauri /usr/local/bin/tauri

# Set CUDA environment
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}
ENV GPU_BACKEND=${PLATFORM}

# Create application directories
RUN mkdir -p /app/{data,models,source_data,normalized,analysis,provenance,config,logs}

# Copy application code
COPY --from=base /opt/venv /opt/venv
COPY src/ /app/src/
COPY tests/ /app/tests/
COPY pyproject.toml /app/pyproject.toml

# Set up Nix path
ENV NIX_PATH=/nix/var/nix/profiles/per-user/root/channels
ENV PATH=/root/.nix-profile/bin:${PATH}

WORKDIR /app

# Expose Tauri dev port
EXPOSE 1420

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import clearthread; print('ClearThread OK')" || exit 1

# Default command
CMD ["clearthread", "serve"]
