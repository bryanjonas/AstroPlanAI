# AstroPlanAI Application Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY examples/ ./examples/
COPY docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Install the package in development mode
RUN pip install -e .

# Create directory for user scripts
RUN mkdir -p /workspace

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/workspace

# Entrypoint script handles VLLM connectivity checks
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - run interactive shell
CMD ["/bin/bash"]
