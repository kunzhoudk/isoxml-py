# ---- build stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .


# ---- runtime stage ----
FROM python:3.11-slim

LABEL org.opencontainers.image.title="isoxml-py" \
      org.opencontainers.image.description="ISOXML TaskData CLI tools" \
      org.opencontainers.image.source="https://github.com/kunzhoudk/isoxml-py"

# Copy installed package from builder
COPY --from=builder /install /usr/local

# Working directory for user data (mount volumes here)
WORKDIR /data

# Smoke-test that the package is importable
RUN python -c "import isoxml"

# Default: drop into a shell so users can run any isoxml-* command.
# Override by passing the command directly, e.g.:
#   docker run --rm -v $(pwd):/data isoxml isoxml-validate-taskdata --help
CMD ["/bin/bash"]
