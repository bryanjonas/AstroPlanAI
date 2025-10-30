#!/bin/bash
# AstroPlanAI Docker Entrypoint
# Connects to external VLLM server running on host machine

set -e

echo "=========================================="
echo "  AstroPlanAI Multi-Agent System"
echo "=========================================="
echo ""
echo "VLLM Endpoint: ${VLLM_BASE_URL}"
echo "Model: ${VLLM_MODEL}"
echo ""

# Extract host and check VLLM connectivity
echo "Checking external VLLM server connectivity..."

# Extract base URL without /v1 suffix for health check
VLLM_HOST=$(echo "${VLLM_BASE_URL}" | sed 's|/v1$||')

max_attempts=15
attempt=0

while [ $attempt -lt $max_attempts ]; do
    # Try both /health and /v1/models endpoints
    if curl -s -f "${VLLM_HOST}/health" > /dev/null 2>&1 || \
       curl -s -f "${VLLM_BASE_URL}/models" > /dev/null 2>&1; then
        echo "✓ External VLLM server is reachable!"

        # Try to verify the model is loaded
        if curl -s -f "${VLLM_BASE_URL}/models" > /dev/null 2>&1; then
            echo "✓ VLLM API endpoint is responding"
        fi
        break
    fi

    attempt=$((attempt + 1))
    echo "  Waiting for VLLM server... (${attempt}/${max_attempts})"
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo ""
    echo "⚠ WARNING: Could not connect to external VLLM server"
    echo ""
    echo "Please ensure:"
    echo "  1. VLLM is running on your host machine"
    echo "  2. VLLM is listening on the correct port (default: 8000)"
    echo "  3. VLLM_BASE_URL in .env points to the correct endpoint"
    echo ""
    echo "To test VLLM manually:"
    echo "  curl http://localhost:8000/health"
    echo "  curl http://localhost:8000/v1/models"
    echo ""
    echo "Container will start anyway, but agents will fail without VLLM."
    echo ""
fi

echo ""
echo "Available commands:"
echo "  - Run basic example: python /app/examples/basic_plan.py"
echo "  - Run tools demo: python /app/examples/simple_query.py"
echo "  - Run tests: pytest /app/tests/"
echo ""
echo "Your workspace is mounted at: /workspace"
echo "=========================================="
echo ""

# Execute the main command
exec "$@"
