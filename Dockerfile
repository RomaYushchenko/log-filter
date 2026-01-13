# Multi-stage build for optimized log-filter container
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt requirements-dev.txt pyproject.toml ./

# Install dependencies in virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY README.md LICENSE ./

# Install package
RUN pip install --no-cache-dir -e .

# Production stage
FROM python:3.12-slim

# Set metadata
LABEL maintainer="yushenkoromaf7@gmail.com"
LABEL description="High-performance log filtering tool with boolean expressions"
LABEL version="2.0.0"

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash logfilter

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy source code (needed for editable install)
COPY --from=builder /app/src /app/src
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/README.md /app/README.md
COPY --from=builder /app/LICENSE /app/LICENSE

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_FILTER_WORKERS=4 \
    LOG_FILTER_BUFFER_SIZE=8192

# Create directories for logs and output
RUN mkdir -p /logs /output && \
    chown -R logfilter:logfilter /logs /output

# Set working directory
WORKDIR /app

# Switch to non-root user
USER logfilter

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import log_filter; print(log_filter.__version__)" || exit 1

# Default command shows help
ENTRYPOINT ["log-filter"]
CMD ["--help"]
