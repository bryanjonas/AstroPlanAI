#!/bin/bash
# Run an example script in the containerized environment

set -e

EXAMPLE=${1:-basic_plan}

echo "Running AstroPlanAI example: ${EXAMPLE}"
echo ""

# Check if docker-compose is running
if ! docker ps | grep -q astroplan-vllm; then
    echo "Error: Docker containers are not running"
    echo "Start them with: docker-compose up -d"
    exit 1
fi

# Run the example
docker-compose exec astroplanai python /app/examples/${EXAMPLE}.py
