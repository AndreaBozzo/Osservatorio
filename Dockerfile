# Osservatorio ISTAT Data Platform - Multi-stage Docker Build
# Production-ready FastAPI application with optimized performance

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels for metadata
LABEL maintainer="Andrea Bozzo <andreabozzo92@gmail.com>"
LABEL org.opencontainers.image.title="Osservatorio ISTAT Data Platform"
LABEL org.opencontainers.image.description="Modern Italian Statistical Data Platform with FastAPI REST API"
LABEL org.opencontainers.image.version=${VERSION:-"1.0.0"}
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.revision=${VCS_REF}
LABEL org.opencontainers.image.vendor="Osservatorio ISTAT"
LABEL org.opencontainers.image.licenses="MIT"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create virtual environment (separate layer for better caching)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip in separate layer (caches better)
RUN pip install --upgrade pip setuptools wheel

# Copy only requirements files first (most stable layer)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies (separate from pip upgrade for better caching)
RUN pip install --no-cache-dir -r requirements.txt

# Copy pyproject.toml separately (less likely to change than app code)
COPY pyproject.toml ./

# Production stage
FROM python:3.11-slim as production

# Install runtime system dependencies and create user in one layer
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r osservatorio \
    && useradd -r -g osservatorio osservatorio

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements files (needed for development stage)
COPY requirements.txt requirements-dev.txt ./

# Copy pyproject.toml
COPY pyproject.toml ./

# Create directories before copying code (static operation, caches well)
RUN mkdir -p data/databases data/cache data/logs logs

# Copy application code excluding frequently changing files
COPY --chown=osservatorio:osservatorio src/ ./src/

# Copy configuration files (less frequently changed)
COPY --chown=osservatorio:osservatorio *.py *.toml *.cfg *.ini ./

# Set ownership in final step
RUN chown -R osservatorio:osservatorio data logs

# Switch to non-root user
USER osservatorio

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    OSSERVATORIO_ENV=production \
    OSSERVATORIO_LOG_LEVEL=INFO

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage
FROM production as development

USER root

# Install development dependencies (requirements files already copied from production stage)
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER osservatorio

# Override for development
ENV OSSERVATORIO_ENV=development \
    OSSERVATORIO_LOG_LEVEL=DEBUG

CMD ["uvicorn", "src.api.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
