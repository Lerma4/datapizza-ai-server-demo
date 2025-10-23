# syntax=docker/dockerfile:1.7

# Base image: light and secure Python runtime
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and ensure unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -u 10001 -m appuser

# Set working directory
WORKDIR /app

# Install uv for fast, reproducible installs from pyproject/lockfile
RUN pip install --no-cache-dir --upgrade pip uv

# Copy dependency manifests first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into system Python using lockfile (no dev deps)
RUN uv export --no-dev --frozen -o requirements.txt
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY main.py ./main.py
COPY README.md ./README.md

# Environment configuration (set secrets at runtime)
# OPENAI_API_KEY must be provided at runtime (or via Docker/K8s secrets)
ENV OPENAI_MODEL=gpt-4o-mini

# Expose FastAPI default port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]