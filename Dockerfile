# This is the Multi-stage Dockerfile for the app-service

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install git for pip to clone repositories
RUN apt-get update \
    && apt-get install -y git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install build dependencies and Python packages
RUN python -m venv /build/venv \
    && /build/venv/bin/pip install --upgrade pip \
    && /build/venv/bin/pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/venv /app/venv

# Copy application code
COPY src/ ./src/

# Set environment variables
ARG APP_VERSION=NOT_SET
ENV APP_VERSION=${APP_VERSION}
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_DEBUG=0

EXPOSE 5000

# Set the entrypoint to the application
# Use the virtual environment's Python interpreter
CMD ["/app/venv/bin/python", "src/main.py"]
